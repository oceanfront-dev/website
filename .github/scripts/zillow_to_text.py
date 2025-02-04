#!/usr/bin/env python3
import os
import sys
import re
import json
import requests
from bs4 import BeautifulSoup
import openai

# Ensure your OPENAI_API_KEY is set in the environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or ""
openai.api_key = OPENAI_API_KEY
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY is missing.", file=sys.stderr)
    sys.exit(1)

# Regex to match lines with "Detail URL:" in the release body.
RE_DETAIL_URL = re.compile(r"Detail URL:\s*(\S+)")

def extract_detail_urls(release_body):
    """Parse the release body and extract all detail URLs."""
    urls = RE_DETAIL_URL.findall(release_body)
    return urls

def fetch_page_text(url):
    """Fetch the URL and extract all visible text from the page."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        # Parse with BeautifulSoup to extract text.
        soup = BeautifulSoup(response.text, "html.parser")
        # Extract all text, stripping extra whitespace.
        text = " ".join(soup.stripped_strings)
        return text
    except Exception as e:
        return f"Error fetching URL {url}: {e}"

def generate_prompt(page_text):
    """
    Build a prompt that instructs ChatGPT to generate a grade for the property
    and a 50-word description.
    """
    prompt = (
        "You are a real estate evaluator. Based on the following property information, "
        "provide a property grade (for example, A, B, C, etc. or a numeric score) and a concise, "
        "50-word description summarizing its key features.\n\n"
        "Property Information:\n"
        f"{page_text}\n\n"
        "Provide your response in the format:\n"
        "Grade: <grade>\n"
        "Description: <50-word description>"
    )
    return prompt

def call_chatgpt(prompt):
    """Call the OpenAI API with the prompt and return the response text."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or another model of your choice
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error calling OpenAI API: {e}"

def main():
    if len(sys.argv) < 2:
        print("Usage: zillow_to_text.py <release_body_file>", file=sys.stderr)
        sys.exit(1)

    release_body_file = sys.argv[1]
    try:
        with open(release_body_file, "r", encoding="utf-8") as f:
            release_body = f.read()
    except Exception as e:
        print(f"Error reading file {release_body_file}: {e}", file=sys.stderr)
        sys.exit(1)

    urls = extract_detail_urls(release_body)
    if not urls:
        print("No detail URLs found in the release body.", file=sys.stderr)
        sys.exit(1)

    results = []
    for url in urls:
        page_text = fetch_page_text(url)
        prompt = generate_prompt(page_text)
        analysis = call_chatgpt(prompt)
        results.append(f"URL: {url}\n{analysis}\n")

    # Output the aggregated analysis for all listings.
    output = "\n".join(results)
    print(output)

if __name__ == "__main__":
    main()
