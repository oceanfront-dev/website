#!/usr/bin/env python3
import os
import sys
import json
import time
import random
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

# File to store the previous total listing count
LAST_COUNT_FILE = ".github/last_count.txt"

# URL to scrape (using the more detailed jupyter notebook version)
SEARCH_URL = (
    "https://www.zillow.com/juno-beach-north-palm-beach-fl/"
    "?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22isMapVisible%22%3Afalse%2C"
    "%22mapBounds%22%3A%7B%22north%22%3A26.905794427212427%2C%22south%22%3A26.844316354071616%2C"
    "%22east%22%3A-80.04391863217162%2C%22west%22%3A-80.07142736782836%7D%2C%22mapZoom%22%3A15%2C"
    "%22regionSelection%22%3A%5B%7B%22regionId%22%3A39182%2C%22regionType%22%3A8%7D%5D%2C"
    "%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22days%22%7D%2C%22doz%22%3A%7B%22value%22%3A%221%22%7D%7D%2C"
    "%22isListVisible%22%3Atrue%7D"
)

class ZillowScraper:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument(
            'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )

    def start_driver(self):
        self.driver = webdriver.Chrome(options=self.options)
        # Prevent detection by overriding the navigator.webdriver property.
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })

    def close_driver(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

    def wait_and_scroll(self):
        """Scrolls the page to ensure that dynamic content loads."""
        SCROLL_PAUSE_TIME = 2
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            time.sleep(random.uniform(1.0, 2.0))

    def get_property_data(self, url):
        try:
            self.start_driver()
            self.driver.get(url)
            time.sleep(5)  # Wait for initial page load

            # Try several CSS selectors to match the property cards.
            possible_selectors = [
                "article[class*='StyledPropertyCard']",
                "div[class*='property-card']",
                "div[class*='ListItem']",
                "div[data-test='property-card']"
            ]
            property_elements = None
            used_selector = None
            for selector in possible_selectors:
                try:
                    wait = WebDriverWait(self.driver, 10)
                    property_elements = wait.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    if property_elements:
                        used_selector = selector
                        break
                except TimeoutException:
                    continue

            if not property_elements:
                print("Could not find property elements with any selector", file=sys.stderr)
                return pd.DataFrame()

            self.wait_and_scroll()
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            properties = []

            for card in soup.select(used_selector):
                property_data = {}

                # Try extracting JSON‑LD data
                scripts = card.find_all("script", type="application/ld+json")
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict):
                            if data.get("@type") == "SingleFamilyResidence":
                                geo_data = data.get('geo', {})
                                property_data.update({
                                    'address': data.get('address', {}).get('streetAddress'),
                                    'city': data.get('address', {}).get('addressLocality'),
                                    'state': data.get('address', {}).get('addressRegion'),
                                    'zip': data.get('address', {}).get('postalCode'),
                                    'floor_size': data.get('floorSize', {}).get('value'),
                                    'url': data.get('url'),
                                    'latitude': geo_data.get('latitude'),
                                    'longitude': geo_data.get('longitude')
                                })
                            elif data.get("@type") == "Event" and 'offers' in data:
                                property_data['price'] = data.get('offers', {}).get('price')
                                if not property_data.get('latitude'):
                                    location = data.get('location', {})
                                    geo_data = location.get('geo', {})
                                    property_data.update({
                                        'latitude': geo_data.get('latitude'),
                                        'longitude': geo_data.get('longitude')
                                    })
                    except (json.JSONDecodeError, AttributeError):
                        continue

                # Fallback to HTML selectors if JSON‑LD is not available
                if not property_data.get('price'):
                    price_elem = card.select_one("[data-test='property-card-price']")
                    if price_elem:
                        property_data['price'] = price_elem.text.strip()

                if not property_data.get('url'):
                    url_elem = card.select_one("a[href*='/homedetails/']")
                    if url_elem:
                        href = url_elem['href']
                        href = href.replace('https://www.zillow.comhttps://www.zillow.com', 'https://www.zillow.com')
                        if href.startswith('/'):
                            property_data['url'] = 'https://www.zillow.com' + href
                        elif href.startswith('http'):
                            property_data['url'] = href
                        else:
                            property_data['url'] = 'https://www.zillow.com/' + href

                update_badge = card.find("span", class_=re.compile("StyledPropertyCardBadge-.*"))
                if update_badge:
                    property_data['last_updated'] = update_badge.text.strip()

                # Build a full address from available parts
                address_parts = []
                if property_data.get('address'):
                    address_parts.append(property_data['address'])
                if property_data.get('city'):
                    address_parts.append(property_data['city'])
                if property_data.get('state'):
                    address_parts.append(property_data['state'])
                if property_data.get('zip'):
                    address_parts.append(property_data['zip'])
                if address_parts:
                    property_data['full_address'] = ', '.join(address_parts)

                # Extract additional stats (beds, baths, sqft)
                stats_div = card.select_one("ul[class*='StyledPropertyCardHomeDetailsList']")
                if stats_div:
                    stats = stats_div.get_text()
                    beds_match = re.search(r'(\d+)\s*bd', stats)
                    baths_match = re.search(r'(\d+)\s*ba', stats)
                    sqft_match = re.search(r'([\d,]+)\s*sqft', stats)
                    if beds_match:
                        property_data['beds'] = beds_match.group(1)
                    if baths_match:
                        property_data['baths'] = baths_match.group(1)
                    if sqft_match:
                        property_data['sqft'] = sqft_match.group(1).replace(',', '')

                # Optionally, extract property type and listing company
                type_div = card.find(text=re.compile(r'(House|Condo|Apartment)\s+for\s+sale'))
                if type_div:
                    m = re.search(r'(House|Condo|Apartment)', type_div)
                    if m:
                        property_data['type'] = m.group(1)
                company_div = card.find("div", class_=re.compile("StyledPropertyCardDataArea-.*"))
                if company_div and not re.search(r'(House|Condo|Apartment)\s+for\s+sale', company_div.text):
                    property_data['listing_company'] = company_div.text.strip()

                if property_data:
                    properties.append(property_data)

            df = pd.DataFrame(properties)
            if not df.empty:
                # (Optional) Mark “direct results” if you can detect the total count from the page.
                try:
                    results_div = soup.find("div", class_=re.compile("search-page-list-header"))
                    num_direct_results = 0
                    if results_div:
                        match = re.search(r'(\d+)\s+results?', results_div.text)
                        if match:
                            num_direct_results = int(match.group(1))
                    df['is_direct_result'] = False
                    if num_direct_results > 0 and len(df) >= num_direct_results:
                        df.loc[:num_direct_results-1, 'is_direct_result'] = True
                except Exception as e:
                    print(f"Error marking direct results: {str(e)}", file=sys.stderr)
                    df['is_direct_result'] = True

                # Clean up the price column (remove non-digit characters)
                if 'price' in df.columns:
                    df['price'] = df['price'].apply(
                        lambda x: re.sub(r'[^\d.]', '', str(x)) if pd.notnull(x) else "N/A"
                    )
            return df

        except Exception as e:
            print(f"An error occurred during scraping: {str(e)}", file=sys.stderr)
            return pd.DataFrame()
        finally:
            self.close_driver()

def load_last_count():
    if not os.path.exists(LAST_COUNT_FILE):
        return 0
    try:
        with open(LAST_COUNT_FILE, "r") as f:
            return int(f.read().strip())
    except ValueError:
        return 0

def save_last_count(count):
    os.makedirs(os.path.dirname(LAST_COUNT_FILE), exist_ok=True)
    with open(LAST_COUNT_FILE, "w") as f:
        f.write(str(count))

def format_release_message(new_count, old_count, records):
    """Formats the release message similar to your example."""
    lines = []
    lines.append("A new increase in Zillow listings was found.")
    lines.append("")
    lines.append(f"We found {new_count} new listing(s) (old record value: {old_count}).")
    lines.append("")
    for i, rec in enumerate(records, start=1):
        # Number the listings in reverse order (newest gets the highest number)
        record_number = old_count + new_count - (i - 1)
        address = rec.get('full_address', rec.get('address', 'N/A'))
        price = rec.get('price', 'N/A')
        url = rec.get('url', 'N/A')
        lines.append(f"New Listing #{record_number}")
        lines.append(f"Address: {address}")
        lines.append(f"Price: {price}")
        lines.append(f"Detail URL: {url}")
        lines.append("")
    return "\n".join(lines)

def main():
    try:
        scraper = ZillowScraper()
        df = scraper.get_property_data(SEARCH_URL)
        current_count = len(df)
        old_count = load_last_count()
        new_listings = current_count - old_count

        print(f"Current count: {current_count}, old count: {old_count}, new listings: {new_listings}", file=sys.stderr)

        # Save the CSV (even if no new listings were found)
        if not df.empty:
            df.to_csv('zillow_properties.csv', index=False)
            print("CSV file 'zillow_properties.csv' generated.")

        github_output = os.environ.get("GITHUB_OUTPUT")
        if new_listings > 0:
            # Assume the newest listings are at the top of the DataFrame.
            new_records = df.head(new_listings).to_dict(orient='records')
            save_last_count(current_count)
            message = format_release_message(new_listings, old_count, new_records)
            if github_output:
                with open(github_output, "a") as fh:
                    fh.write("new_data=true\n")
                    fh.write("details<<EOF\n")
                    fh.write(message + "\n")
                    fh.write("EOF\n")
        else:
            if github_output:
                with open(github_output, "a") as fh:
                    fh.write("new_data=false\n")
                    fh.write("details=No new listings found.\n")
    except Exception as e:
        print(f"Error in main: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
