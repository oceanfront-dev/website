#!/usr/bin/env python3
import os
import re
import sys
import logging
import time
from bs4 import BeautifulSoup

try:
    from openai import OpenAI
except ImportError:
    logging.error("Error: The 'openai' library (or your custom O1-mini package) is missing.")
    sys.exit(1)

# Set up basic debugging logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

# Get the OpenAI API key from the environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    logging.error("Error: OPENAI_API_KEY is missing.")
    sys.exit(1)

# Initialize the OpenAI client using your custom interface (as in ct_to_text.py)
client = OpenAI(api_key=OPENAI_API_KEY)

# Regex to extract detail URLs from the release body
RE_DETAIL_URL = re.compile(r"Detail URL:\s*(\S+)", re.IGNORECASE)

# The working search URL from your first workflow
MAIN_SEARCH_URL = (
    "https://www.zillow.com/juno-beach-fl/?searchQueryState=%7B%22regionSelection%22%3A%5B%7B"
    "%22regionId%22%3A39182%2C%22regionType%22%3A8%7D%5D%2C%22filterState%22%3A%7B%22doz%22%3A"
    "%7B%22value%22%3A%221%22%7D%2C%22sort%22%3A%7B%22value%22%3A%22days%22%7D%7D%7D"
)

def extract_urls(body: str):
    """
    Parse the release body and return a list of detail URLs.
    Expected format in the release body:
      Detail URL: https://www.zillow.com/homedetails/...
    """
    urls = RE_DETAIL_URL.findall(body)
    logging.debug(f"Extracted URLs: {urls}")
    return urls

def extract_metadata(html_text: str) -> str:
    """
    Extract metadata elements from the HTML:
      - The <title> text
      - The content of the <meta property="zillow_fb:description"> tag
    Returns a string combining these elements.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    title = soup.title.text.strip() if soup.title and soup.title.text else ""
    meta_desc = ""
    meta_tag = soup.find("meta", property="zillow_fb:description")
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()
    combined = f"Title: {title}\nMeta Description: {meta_desc}"
    return combined

def fetch_page_text(url: str) -> str:
    """
    Load the Zillow page using Selenium.
    First, navigate to MAIN_SEARCH_URL and wait to simulate natural browsing.
    Then, navigate to the given detail URL with a delay.
    Finally, extract metadata (title and meta description) from the page.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError as ie:
        logging.error("Selenium or webdriver_manager not available.")
        return "Error: Selenium not available."
    
    try:
        logging.debug("Initializing Selenium WebDriver using Service.")
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # First, visit the main search URL to simulate natural browsing.
        logging.debug(f"Navigating to MAIN_SEARCH_URL: {MAIN_SEARCH_URL}")
        driver.get(MAIN_SEARCH_URL)
        time.sleep(5)  # Wait 5 seconds
        
        # Then, navigate to the detail URL.
        logging.debug(f"Navigating to detail URL: {url}")
        driver.get(url)
        time.sleep(5)  # Wait 5 seconds to simulate natural click delay
        
        # Get the page source and extract metadata.
        html_text = driver.page_source
        driver.quit()
        metadata = extract_metadata(html_text)
        logging.debug("Successfully fetched metadata using Selenium.")
        return metadata
    except Exception as se:
        logging.error(f"Selenium method failed for URL {url}: {se}")
        return f"Error fetching URL {url} using Selenium: {se}"

def generate_prompt(page_text: str) -> str:
    """
    Construct a prompt instructing the model to return a property grade on the first line
    and an exactly 50-word description on the second line, using the provided metadata.
    """
    prompt = (
        "You are a real estate evaluator. Analyze the following property metadata and respond in exactly two lines, with no additional commentary:\n\n"
        "1. The first line must contain only the property grade (e.g., A, B, C, or a numeric score).\n"
        "2. The second line must contain a property description that is exactly 50 words long, summarizing the property's key features.\n\n"
        "Use this exact format:\n"
        "Grade: <grade>\n"
        "Description: <50-word description>\n\n"
        "Property Metadata:\n"
        f"{page_text}\n\n"
        "Ensure that the description is exactly 50 words and nothing else is added."
    )
    logging.debug(f"Generated prompt (first 200 chars): {prompt[:200]}...")
    return prompt

def get_analysis_for_url(url: str) -> str:
    """
    For a given property URL, load the page via Selenium, extract metadata,
    build a prompt, and call the OpenAI API to generate the analysis.
    """
    logging.debug(f"Starting analysis for URL: {url}")
    metadata = fetch_page_text(url)
    prompt = generate_prompt(metadata)
    try:
        resp = client.chat.completions.create(
            model="o1-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = resp.choices[0].message.content.strip()
        logging.debug(f"Received analysis for URL: {url}")
        return analysis
    except Exception as e:
        logging.error(f"Error calling OpenAI API for URL {url}: {e}")
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
