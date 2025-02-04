#!/usr/bin/env python3
import os
import sys
import requests
from lxml import html
import json

# Zillow URL with URL-encoded query state
SEARCH_URL = (
    "https://www.zillow.com/juno-beach-fl/?searchQueryState="
    "%7B%22regionSelection%22%3A%5B%7B%22regionId%22%3A39182%2C%22regionType%22%3A8%7D%5D%2C"
    "%22filterState%22%3A%7B%22doz%22%3A%7B%22value%22%3A%221%22%7D%2C%22sort%22%3A%7B%22value%22%3A%22days%22%7D%7D%7D"
)
LAST_COUNT_FILE = ".github/last_count.txt"
# XPath to get the count element (unchanged)
XPATH_COUNT = "/html/body/div[1]/div/div[2]/div/div/div[1]/div[1]/div[1]/div/span"
# XPath to select each listing <li> element (from which we will extract the JSON from its child <script> tag)
XPATH_LISTINGS = "/html/body/div[1]/div/div[2]/div/div/div[1]/div[1]/ul/li"

def get_page_doc():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    response = requests.get(SEARCH_URL, headers=headers, timeout=30)
    response.raise_for_status()
    return html.fromstring(response.content)

def get_current_listing_count(doc):
    count_elements = doc.xpath(XPATH_COUNT)
    if count_elements:
        count_text = count_elements[0].text_content().strip()
        count_numeric = ''.join(filter(str.isdigit, count_text))
        if count_numeric:
            return int(count_numeric)
        else:
            raise ValueError(f"No numeric count found in element text: '{count_text}'")
    else:
        raise ValueError("XPath element for count not found in the page.")

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

def parse_new_listings(new_count, doc):
    # Get the first new_count <li> elements
    li_elements = doc.xpath(XPATH_LISTINGS)[:new_count]
    records = []
    for li in li_elements:
        record = {}
        # Try to extract JSON from the <script> tag inside this listing.
        # (The XPath below finds the script inside the nested <div> elements.)
        script_elements = li.xpath(".//div/div/script")
        if script_elements:
            json_text = script_elements[0].text_content().strip()
            try:
                listing_data = json.loads(json_text)
                record["detail_url"] = listing_data.get("url", "N/A")
                record["address"] = listing_data.get("name", "N/A")
            except Exception as e:
                record["detail_url"] = "N/A"
                record["address"] = "N/A"
        else:
            record["detail_url"] = "N/A"
            record["address"] = "N/A"
        # Optionally, try to extract the price from an element with class 'list-card-price'
        price_elements = li.xpath(".//*[contains(@class,'list-card-price')]")
        if price_elements:
            record["price"] = price_elements[0].text_content().strip()
        else:
            record["price"] = "N/A"
        records.append(record)
    return records

def format_release_message(new_records, old_count, records):
    lines = []
    lines.append("A new increase in Zillow listings was found.")
    lines.append("")
    lines.append(f"We found {new_records} new listing(s) (old record value: {old_count}).")
    lines.append("")
    for i, rec in enumerate(records, start=1):
        record_number = old_count + new_records - (i - 1)
        lines.append(f"New Listing #{record_number}")
        lines.append(f"Address: {rec.get('address', 'N/A')}")
        lines.append(f"Price: {rec.get('price', 'N/A')}")
        lines.append(f"Detail URL: {rec.get('detail_url', 'N/A')}")
        lines.append("")
    return "\n".join(lines)

def main():
    try:
        doc = get_page_doc()
        current_count = get_current_listing_count(doc)
        old_count = load_last_count()
        new_listings = current_count - old_count
        print(f"Current count: {current_count}, old count: {old_count}, new listings: {new_listings}", file=sys.stderr)
        if new_listings > 0:
            new_records = parse_new_listings(new_listings, doc)
            save_last_count(current_count)
            message = format_release_message(new_listings, old_count, new_records)
            # Write output for GitHub Actions via GITHUB_OUTPUT file.
            github_output = os.environ.get("GITHUB_OUTPUT")
            if github_output:
                with open(github_output, "a") as fh:
                    fh.write("new_data=true\n")
                    fh.write("details<<EOF\n")
                    fh.write(message + "\n")
                    fh.write("EOF\n")
        else:
            github_output = os.environ.get("GITHUB_OUTPUT")
            if github_output:
                with open(github_output, "a") as fh:
                    fh.write("new_data=false\n")
                    fh.write("details=No new listings found.\n")
    except Exception as e:
        print(f"Error in main: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
