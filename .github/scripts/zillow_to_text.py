#!/usr/bin/env python3
import os
import sys
import openai
import re

# Set your OpenAI API key from the environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY is missing.")
    sys.exit(1)

openai.api_key = OPENAI_API_KEY

# A regex to detect new listing headers (e.g., "New Listing #<number>")
RE_LISTING_HEADER = re.compile(r'^New Listing #(\d+)', re.IGNORECASE)

def parse_listings_from_body(body: str):
    """
    Parse the release body for listing details.
    Expected lines (for each listing):
      New Listing #<number>
      Address: <address>
      Price: <price>
      Detail URL: <url>
    """
    listings = []
    current_listing = {}
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        header_match = RE_LISTING_HEADER.match(line)
        if header_match:
            if current_listing:
                listings.append(current_listing)
            current_listing = {"listing_number": header_match.group(1)}
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            current_listing[key.strip().lower()] = value.strip()
    if current_listing:
        listings.append(current_listing)
    return listings

def generate_analysis_for_listings(listings):
    if not listings:
        return "No new listings to analyze."
    
    prompt = "You are a real estate market analyst. Analyze the following Zillow listing data and provide insights about market trends, pricing, and potential investment opportunities. Provide a detailed, multi-paragraph analysis for each listing.\n\n"
    for listing in listings:
        prompt += (
            f"Listing #{listing.get('listing_number', 'N/A')}: "
            f"Address: {listing.get('address', 'N/A')}, "
            f"Price: {listing.get('price', 'N/A')}, "
            f"Detail URL: {listing.get('detail url', 'N/A')}\n\n"
        )
    prompt += "Please provide a clear and informative analysis."
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error calling OpenAI API: {e}"

def main():
    if len(sys.argv) < 2:
        print("Usage: zillow_to_text.py <release_body_file>")
        sys.exit(1)
    release_body_file = sys.argv[1]
    if not os.path.isfile(release_body_file):
        print(f"File '{release_body_file}' not found.")
        sys.exit(1)
    with open(release_body_file, "r", encoding="utf-8") as f:
        body = f.read()
    listings = parse_listings_from_body(body)
    analysis = generate_analysis_for_listings(listings)
    print(analysis)

if __name__ == "__main__":
    main()
