#!/usr/bin/env python3
import os
import sys
import time
import requests
from lxml import html

SEARCH_URL = (
    "https://www.zillow.com/juno-beach-fl/?searchQueryState="
    "%7B%22regionSelection%22%3A%5B%7B%22regionId%22%3A39182%2C%22regionType%22%3A8%7D%5D%2C"
    "%22filterState%22%3A%7B%22doz%22%3A%7B%22value%22%3A%221%22%7D%2C%22sort%22%3A%7B%22value%22%3A%22days%22%7D%7D%7D"
)
LAST_COUNT_FILE = ".github/last_count.txt"
XPATH_COUNT = "/html/body/div[1]/div/div[2]/div/div/div[1]/div[1]/div[1]/div/span"

def get_current_listing_count():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    try:
        response = requests.get(SEARCH_URL, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        raise

    try:
        doc = html.fromstring(response.content)
        count_elements = doc.xpath(XPATH_COUNT)
        if count_elements:
            count_text = count_elements[0].text_content().strip()
            count_numeric = ''.join(filter(str.isdigit, count_text))
            if count_numeric:
                return int(count_numeric)
            else:
                raise ValueError(f"No numeric count found in element text: '{count_text}'")
        else:
            raise ValueError("XPath element not found in the page.")
    except Exception as e:
        print(f"Error parsing HTML: {e}", file=sys.stderr)
        raise

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

def main():
    try:
        current_count = get_current_listing_count()
        old_count = load_last_count()
        new_listings = current_count - old_count
        print(f"Current count: {current_count}, old count: {old_count}, new listings: {new_listings}", file=sys.stderr)
        if new_listings > 0:
            save_last_count(current_count)
            github_output = os.environ.get("GITHUB_OUTPUT")
            if github_output:
                with open(github_output, "a") as fh:
                    fh.write("new_data=true\n")
                    fh.write("details<<EOF\n")
                    fh.write(f"Found {new_listings} new listing(s) on Zillow.\n")
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
