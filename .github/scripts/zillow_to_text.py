#!/usr/bin/env python3
import os
import re
import sys
import requests
from bs4 import BeautifulSoup

try:
    from openai import OpenAI
except ImportError:
    print("Error: The 'openai' library (or your custom O1-mini package) is missing.")
    sys.exit(1)

# Get the OpenAI API key from the environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY is missing.", file=sys.stderr)
    sys.exit(1)

# Initialize the client (using the same pattern as in your ct_to_text.py script)
client = OpenAI(api_key=OPENAI_API_KEY)

# Regex to extract detail URLs from the release body
RE_DETAIL_URL = re.compile(r"Detail URL:\s*(\S+)", re.IGNORECASE)

def extract_urls(body: str):
    """
    Parses the release body and returns a list of detail URLs.
    Expected lines in the release body:
      Detail URL: https://www.zillow.com/homedetails/...
    """
    return RE_DETAIL_URL.findall(body)

def fetch_page_text(url: str) -> str:
    """
    Fetches the Zillow page at the given URL and extracts all visible text.
    """
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
        # Use BeautifulSoup to extract all visible text
        soup = BeautifulSoup(response.text, "html.parser")
        text = " ".join(soup.stripped_strings)
        return text
    except Exception as e:
        return f"Error fetching URL {url}: {e}"

def generate_prompt(page_text: str) -> str:
    """
    Constructs a prompt instructing the model to return a property grade and an exactly 50-word description.
    """
    prompt = (
        "You are a real estate evaluator. Based on the following property details, "
        "provide a property grade (e.g., A, B, C, or a numeric score) and a concise, exactly 50-word description summarizing the property's key features.\n\n"
        "Property Information:\n"
        f"{page_text}\n\n"
        "Respond strictly in the format:\n"
        "Grade: <grade>\n"
        "Description: <50-word description>"
    )
    return prompt

def get_analysis_for_url(url: str) -> str:
    """
    For a given property URL, fetches the page text, builds a prompt, and calls the OpenAI API.
    """
    page_text = fetch_page_text(url)
    prompt = generate_prompt(page_text)
    try:
        # Using the same API call style as in your ct_to_text.py script:
        resp = client.chat.completions.create(
            model="o1-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Error calling OpenAI API for URL {url}: {e}"

def main():
    if len(sys.argv) < 2:
        print("Usage: zillow_to_text.py <release_body_file>", file=sys.stderr)
        sys.exit(1)

    release_body_file = sys.argv[1]
    if not os.path.isfile(release_body_file):
        print(f"File '{release_body_file}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(release_body_file, "r", encoding="utf-8") as f:
            body = f.read()
    except Exception as e:
        print(f"Error reading file {release_body_file}: {e}", file=sys.stderr)
        sys.exit(1)

    urls = extract_urls(body)
    if not urls:
        print("No detail URLs found in the release body.", file=sys.stderr)
        sys.exit(1)

    results = []
    for url in urls:
        analysis = get_analysis_for_url(url)
        results.append(f"URL: {url}\n{analysis}\n")

    output = "\n".join(results)
    print(output)

if __name__ == "__main__":
    main()
