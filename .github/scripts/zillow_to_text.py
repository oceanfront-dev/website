#!/usr/bin/env python3
import os
import re
import sys
import logging
import requests
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

def extract_urls(body: str):
    """
    Parse the release body and return a list of detail URLs.
    Expected format in the release body:
      Detail URL: https://www.zillow.com/homedetails/...
    """
    urls = RE_DETAIL_URL.findall(body)
    logging.debug(f"Extracted URLs: {urls}")
    return urls

def fetch_page_text(url: str) -> str:
    """
    Fetch the Zillow page at the given URL using human-like request headers.
    If the requests method returns a 403, fall back to Selenium and simulate
    a human clicking a verification button (e.g., a "I am not a robot" button).
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        logging.debug(f"Attempting to fetch URL using requests: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 403 or "403 Forbidden" in response.text:
            logging.debug(f"Requests method returned 403 for URL: {url}")
            raise Exception("403 Forbidden encountered with requests")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        text = " ".join(soup.stripped_strings)
        logging.debug("Successfully fetched page text using requests.")
        return text
    except Exception as e:
        logging.debug(f"Requests method failed for {url} with error: {e}")
        # Fallback: Use Selenium to mimic human behavior.
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
        except ImportError as ie:
            logging.error("Selenium or webdriver_manager not available.")
            return f"Error: Selenium not available. Original error: {e}"

        try:
            logging.debug("Initializing Selenium WebDriver.")
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            # Initialize the driver with ChromeDriverManager
            driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
            driver.get(url)

            # Wait briefly for the page to load.
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Attempt to find and click the verification button if it exists.
            try:
                # Adjust the XPath below to match the actual verification button.
                verification_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'I am not a robot')]"))
                )
                logging.debug("Verification button found; simulating human click-and-hold.")
                actions = ActionChains(driver)
                actions.click_and_hold(verification_button).pause(3).release().perform()
                # Wait a few seconds for the page to update after clicking.
                WebDriverWait(driver, 5).until(
                    EC.invisibility_of_element(verification_button)
                )
            except Exception as ve:
                logging.debug(f"No verification button found or error clicking it: {ve}")

            # After handling the verification, get the page text.
            page_text = driver.find_element(By.TAG_NAME, "body").text
            driver.quit()
            logging.debug("Successfully fetched page text using Selenium.")
            return page_text
        except Exception as se:
            logging.error(f"Selenium method also failed for URL {url}: {se}")
            return f"Error fetching URL {url} using both methods: {e}; Selenium error: {se}"

def generate_prompt(page_text: str) -> str:
    """
    Construct a prompt instructing the model to return a property grade
    and an exactly 50-word description.
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
    logging.debug(f"Generated prompt (first 200 chars): {prompt[:200]}...")
    return prompt

def get_analysis_for_url(url: str) -> str:
    """
    For a given property URL, fetch the page text, build a prompt,
    and call the OpenAI API to generate the analysis.
    """
    logging.debug(f"Starting analysis for URL: {url}")
    page_text = fetch_page_text(url)
    prompt = generate_prompt(page_text)
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
