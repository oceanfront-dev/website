#!/usr/bin/env python3
import os
import requests
import sys
import time
from bs4 import BeautifulSoup

# The Zillow URL. (Note: the JSON must be URL‑encoded.)
SEARCH_URL = (
    "https://www.zillow.com/juno-beach-fl/?searchQueryState="
    "%7B%22regionSelection%22%3A%5B%7B%22regionId%22%3A39182%2C%22regionType%22%3A8%7D%5D%2C"
    "%22filterState%22%3A%7B%22doz%22%3A%7B%22value%22%3A%221%22%7D%2C%22sort%22%3A%7B%22value%22%3A%22days%22%7D%7D%7D"
)
LAST_COUNT_FILE = ".github/last_count.txt"

def get_current_listing_count():
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(SEARCH_URL, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    # Example: assume each listing is contained in an <article> with class "list-card"
    listings = soup.find_all("article", class_="list-card")
    return len(listings), listings

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

def parse_new_listings(new_count, listings):
    """
    Extracts metadata from the first 'new_count' listings.
    Adjust the CSS selectors as needed.
    """
    records = []
    for listing in listings[:new_count]:
        record = {}
        # Try to get the address (if in an <address> tag)
        addr = listing.find("address")
        record["address"] = addr.get_text(strip=True) if addr else "No address"
        # Try to get the price (if in a tag with class "list-card-price")
        price_tag = listing.find(class_="list-card-price")
        record["price"] = price_tag.get_text(strip=True) if price_tag else "N/A"
        # Get the detail URL from an <a> tag with class "list-card-link"
        link_tag = listing.find("a", class_="list-card-link")
        if link_tag and link_tag.get("href"):
            url = link_tag.get("href")
            if url.startswith("/"):
                url = "https://www.zillow.com" + url
            record["detail_url"] = url
        else:
            record["detail_url"] = "N/A"
        records.append(record)
    return records

def format_release_message(new_records, old_count, records):
    lines = []
    lines.append("New Zillow listings detected.")
    lines.append("")
    lines.append(f"Found {new_records} new listing(s) (previous count: {old_count}).")
    lines.append("")
    for i, rec in enumerate(records, start=1):
        listing_number = old_count + new_records - (i - 1)
        lines.append(f"New Listing #{listing_number}")
        lines.append(f"Address: {rec.get('address', 'N/A')}")
        lines.append(f"Price: {rec.get('price', 'N/A')}")
        lines.append(f"Detail URL: {rec.get('detail_url', 'N/A')}")
        lines.append("")
    return "\n".join(lines)

def main():
    try:
        current_count, listings = get_current_listing_count()
        old_count = load_last_count()
        new_listings_count = current_count - old_count

        if new_listings_count > 0:
            new_records = parse_new_listings(new_listings_count, listings)
            save_last_count(current_count)
            message = format_release_message(new_listings_count, old_count, new_records)
            # Write GitHub Actions output
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
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as fh:
                fh.write("new_data=false\n")
                fh.write(f"details=Error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
