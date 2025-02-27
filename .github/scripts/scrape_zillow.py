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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# File to store the previous total listing count
LAST_COUNT_FILE = ".github/last_count.txt"

# URL to scrape (using the detailed query string)
SEARCH_URL = (
    "https://www.zillow.com/juno-beach-north-palm-beach-fl/"
    "?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22isMapVisible%22%3Afalse%2C"
    "%22mapBounds%22%3A%7B%22north%22%3A26.905794427212427%2C%22south%22%3A26.844316354071616%2C"
    "%22east%22%3A-80.04391863217163%2C%22west%22%3A-80.07142736782837%7D%2C%22mapZoom%22%3A15%2C"
    "%22regionSelection%22%3A%5B%7B%22regionId%22%3A39182%2C%22regionType%22%3A8%7D%5D%2C"
    "%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22days%22%7D%2C%22doz%22%3A%7B%22value%22%3A%221%22%7D%7D%2C"
    "%22isListVisible%22%3Atrue%7D"
)

# Directory for screenshots
SCREENSHOT_DIR = "screenshots"

class ZillowScraper:
    def __init__(self):
        # Set up Chrome options with headless mode and anti-detection measures.
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
        
        # Create screenshots directory if it doesn't exist
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    def start_driver(self):
        self.driver = webdriver.Chrome(options=self.options)
        # Override the navigator.webdriver property to help prevent detection.
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        # Set window size to ensure proper rendering
        self.driver.set_window_size(1920, 1080)

    def close_driver(self):
        if hasattr(self, 'driver'):
            self.driver.quit()
            
    def take_screenshot(self, name="zillow_page"):
        """Takes a screenshot of the current page state"""
        if not hasattr(self, 'driver'):
            return None
            
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{SCREENSHOT_DIR}/{name}_{timestamp}.png"
        try:
            self.driver.save_screenshot(filename)
            print(f"Screenshot saved to {filename}", file=sys.stderr)
            return filename
        except Exception as e:
            print(f"Failed to take screenshot: {str(e)}", file=sys.stderr)
            return None

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
            print(f"Navigating to {url}", file=sys.stderr)
            self.driver.get(url)
            
            # Take initial screenshot after page load
            self.take_screenshot("initial_load")
            
            # Wait longer for initial page load
            time.sleep(10)
            
            # Check for captcha or other blocking elements
            if "captcha" in self.driver.page_source.lower() or "robot" in self.driver.page_source.lower():
                print("Captcha detected! Taking screenshot...", file=sys.stderr)
                self.take_screenshot("captcha_detected")
                return pd.DataFrame()
            
            # Try several CSS selectors to match the property cards.
            possible_selectors = [
                "article[class*='StyledPropertyCard']",
                "div[class*='property-card']",
                "div[class*='ListItem']",
                "div[data-test='property-card']",
                "li[data-test='search-result-list-item']",
                "div[id*='search-result-list-item']",
                "div[class*='result-list-item']"
            ]
            
            property_elements = None
            used_selector = None
            
            # Take screenshot before trying selectors
            self.take_screenshot("before_selectors")
            
            for selector in possible_selectors:
                try:
                    print(f"Trying selector: {selector}", file=sys.stderr)
                    wait = WebDriverWait(self.driver, 10)
                    property_elements = wait.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    if property_elements:
                        used_selector = selector
                        print(f"Found {len(property_elements)} elements with selector: {selector}", file=sys.stderr)
                        break
                except TimeoutException:
                    print(f"Timeout with selector: {selector}", file=sys.stderr)
                    continue

            if not property_elements:
                print("Could not find property elements with any selector", file=sys.stderr)
                # Take screenshot of the failed page
                self.take_screenshot("no_elements_found")
                
                # Try to extract page source for debugging
                with open(f"{SCREENSHOT_DIR}/page_source.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                print(f"Page source saved to {SCREENSHOT_DIR}/page_source.html", file=sys.stderr)
                
                # Check if we have any previous data to return
                old_data_path = 'zillow_properties.csv'
                if os.path.exists(old_data_path):
                    print(f"Returning previous data from {old_data_path}", file=sys.stderr)
                    return pd.read_csv(old_data_path)
                return pd.DataFrame()

            self.wait_and_scroll()
            
            # Take screenshot after scrolling
            self.take_screenshot("after_scroll")
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            properties = []

            # Loop through each property card found.
            for card in soup.select(used_selector):
                property_data = {}

                # First, try to extract JSON‑LD data
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
                                # If geo-data isn't set, try getting it from the location.
                                if not property_data.get('latitude'):
                                    location = data.get('location', {})
                                    geo_data = location.get('geo', {})
                                    property_data.update({
                                        'latitude': geo_data.get('latitude'),
                                        'longitude': geo_data.get('longitude')
                                    })
                    except (json.JSONDecodeError, AttributeError):
                        continue

                # Fallback to direct HTML extraction if JSON‑LD did not provide the price.
                if not property_data.get('price'):
                    price_elem = card.select_one("[data-test='property-card-price']")
                    if price_elem:
                        property_data['price'] = price_elem.text.strip()
                    else:
                        # Try alternative price selectors
                        alt_price_selectors = [
                            "span[data-test='price']", 
                            "span[class*='Price']",
                            "div[class*='price']"
                        ]
                        for price_selector in alt_price_selectors:
                            price_elem = card.select_one(price_selector)
                            if price_elem:
                                property_data['price'] = price_elem.text.strip()
                                break

                # Ensure we have the property URL.
                if not property_data.get('url'):
                    url_elem = card.select_one("a[href*='/homedetails/']")
                    if url_elem:
                        href = url_elem['href']
                        # Clean up the URL if necessary.
                        href = href.replace('https://www.zillow.comhttps://www.zillow.com', 'https://www.zillow.com')
                        if href.startswith('/'):
                            property_data['url'] = 'https://www.zillow.com' + href
                        elif href.startswith('http'):
                            property_data['url'] = href
                        else:
                            property_data['url'] = 'https://www.zillow.com/' + href
                    else:
                        # Try alternative URL selectors
                        alt_url_selectors = ["a[href*='zpid']", "a[class*='property-card-link']"]
                        for url_selector in alt_url_selectors:
                            url_elem = card.select_one(url_selector)
                            if url_elem and 'href' in url_elem.attrs:
                                href = url_elem['href']
                                if href.startswith('/'):
                                    property_data['url'] = 'https://www.zillow.com' + href
                                elif href.startswith('http'):
                                    property_data['url'] = href
                                else:
                                    property_data['url'] = 'https://www.zillow.com/' + href
                                break

                # Extract the "last updated" badge text if available.
                update_badge = card.find("span", class_=re.compile("StyledPropertyCardBadge-.*"))
                if update_badge:
                    property_data['last_updated'] = update_badge.text.strip()

                # Try to extract address if not already found
                if not property_data.get('address'):
                    address_elem = card.select_one("[data-test='property-card-addr']")
                    if address_elem:
                        full_address = address_elem.text.strip()
                        property_data['full_address'] = full_address
                        # Try to parse out components
                        address_parts = full_address.split(',')
                        if len(address_parts) >= 1:
                            property_data['address'] = address_parts[0].strip()
                        if len(address_parts) >= 2:
                            property_data['city'] = address_parts[1].strip()
                        if len(address_parts) >= 3:
                            state_zip = address_parts[2].strip().split()
                            if len(state_zip) >= 1:
                                property_data['state'] = state_zip[0]
                            if len(state_zip) >= 2:
                                property_data['zip'] = state_zip[1]
                else:
                    # Build a full address from available address parts.
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

                # Extract additional statistics (beds, baths, sqft) from details.
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
                else:
                    # Try alternative selectors for property details
                    beds_elem = card.select_one("[data-test='property-card-beds']")
                    if beds_elem:
                        beds_text = beds_elem.text.strip()
                        beds_match = re.search(r'(\d+)', beds_text)
                        if beds_match:
                            property_data['beds'] = beds_match.group(1)
                    
                    baths_elem = card.select_one("[data-test='property-card-baths']")
                    if baths_elem:
                        baths_text = baths_elem.text.strip()
                        baths_match = re.search(r'(\d+)', baths_text)
                        if baths_match:
                            property_data['baths'] = baths_match.group(1)
                    
                    sqft_elem = card.select_one("[data-test='property-card-sqft']")
                    if sqft_elem:
                        sqft_text = sqft_elem.text.strip()
                        sqft_match = re.search(r'([\d,]+)', sqft_text)
                        if sqft_match:
                            property_data['sqft'] = sqft_match.group(1).replace(',', '')

                # Optionally, extract property type.
                type_div = card.find(text=re.compile(r'(House|Condo|Apartment)\s+for\s+sale'))
                if type_div:
                    m = re.search(r'(House|Condo|Apartment)', type_div)
                    if m:
                        property_data['type'] = m.group(1)

                # Optionally, extract the listing company.
                company_div = card.find("div", class_=re.compile("StyledPropertyCardDataArea-.*"))
                if company_div and not re.search(r'(House|Condo|Apartment)\s+for\s+sale', company_div.text):
                    property_data['listing_company'] = company_div.text.strip()

                if property_data:
                    properties.append(property_data)

            # Convert the list of properties into a DataFrame.
            df = pd.DataFrame(properties)
            if not df.empty:
                print(f"Found {len(df)} properties", file=sys.stderr)
                
                # Mark "direct results" if possible.
                try:
                    results_div = soup.find("div", class_=re.compile("search-page-list-header"))
                    num_direct_results = 0
                    if results_div:
                        match = re.search(r'(\d+)\s+results?', results_div.text)
                        if match:
                            num_direct_results = int(match.group(1))
                    df['is_direct_result'] = False
                    if num_direct_results > 0 and len(df) >= num_direct_results:
                        df.loc[:num_direct_results - 1, 'is_direct_result'] = True
                except Exception as e:
                    print(f"Error marking direct results: {str(e)}", file=sys.stderr)
                    df['is_direct_result'] = True

                # Clean up the price column: remove any non-digit characters.
                if 'price' in df.columns:
                    df['price'] = df['price'].apply(
                        lambda x: re.sub(r'[^\d.]', '', str(x)) if pd.notnull(x) else None
                    )

                # Convert several columns to numeric types where applicable.
                numeric_columns = ['price', 'beds', 'baths', 'sqft', 'latitude', 'longitude']
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                print("No properties found in the parsed HTML", file=sys.stderr)
                self.take_screenshot("no_properties_parsed")

            return df

        except Exception as e:
            print(f"An error occurred during scraping: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self.take_screenshot("error_screenshot")
            
            # Check if we have any previous data to return
            old_data_path = 'zillow_properties.csv'
            if os.path.exists(old_data_path):
                print(f"Returning previous data from {old_data_path}", file=sys.stderr)
                return pd.read_csv(old_data_path)
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
    """Formats a release message including details of the new listings."""
    lines = []
    lines.append("A new increase in Zillow listings was found.")
    lines.append("")
    lines.append(f"We found {new_count} new listing(s) (old record value: {old_count}).")
    lines.append("")
    for i, rec in enumerate(records, start=1):
        # Number the listings in reverse order (newest gets the highest number).
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
        
        if df.empty:
            print("No data retrieved from scraper", file=sys.stderr)
            github_output = os.environ.get("GITHUB_OUTPUT")
            if github_output:
                with open(github_output, "a") as fh:
                    fh.write("new_data=false\n")
                    fh.write("details=Failed to retrieve data from Zillow.\n")
            return
            
        current_count = len(df)
        old_count = load_last_count()
        new_listings = current_count - old_count

        print(f"Current count: {current_count}, old count: {old_count}, new listings: {new_listings}", file=sys.stderr)

        # Save the CSV file (even if no new listings were found)
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
                print("\nRelease Message:\n")
                print(message)
        else:
            if github_output:
                with open(github_output, "a") as fh:
                    fh.write("new_data=false\n")
                    fh.write("details=No new listings found.\n")
            else:
                print("No new listings found.")
    except Exception as e:
        print(f"Error in main: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
