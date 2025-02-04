#!/usr/bin/env python3
import os
import sys
import re
import pandas as pd

try:
    from openai import OpenAI
except ImportError:
    print("Error: The 'openai' library (or your custom O1-mini package) is missing.")
    sys.exit(1)

# Retrieve the API key from the environment.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY is missing.")
    sys.exit(1)

# Initialize the OpenAI-like client.
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_summary_for_property(row):
    """
    For a given property row, builds a super prompt and calls the OpenAI API
    to generate a compelling 150-word property description along with a uniqueness/rarity score.
    Expected output format from the API is a multi-line text such as:
    
      **Summary:**
      <summary text possibly spanning multiple lines>
      **Uniqueness Score:** <score>
    
    This function uses a regex to capture all the summary text and the uniqueness score.
    It returns a tuple (summary, uniqueness_score).
    """
    price = row.get("price", "N/A")
    url = row.get("url", "N/A")
    last_updated = row.get("last_updated", "N/A")
    beds = row.get("beds", "N/A")
    baths = row.get("baths", "N/A")
    sqft = row.get("sqft", "N/A")
    property_type = row.get("type", "N/A")
    listing_company = row.get("listing_company", "N/A")
    
    # Super prompt for a compelling description and uniqueness score.
    prompt = (
        "You are a top-tier real estate analyst and luxury property marketer. "
        "Below are details for a unique property:\n"
        f"Price: {price}\n"
        f"URL: {url}\n"
        f"Last Updated: {last_updated}\n"
        f"Beds: {beds}\n"
        f"Baths: {baths}\n"
        f"Square Feet: {sqft}\n"
        f"Type: {property_type}\n"
        f"Listing Company: {listing_company}\n\n"
        "Craft a compelling, vivid, and detailed description of this property in approximately 150 words. "
        "Emphasize its unique architectural features, location advantages, and the lifestyle it offers. "
        "Use engaging and persuasive language to capture the essence of the property and evoke a sense of exclusivity and luxury. "
        "Additionally, evaluate the property's distinctiveness and market rarity, and assign a uniqueness/rarity score expressed as a percentage "
        "that reflects how exceptional and rare this property is compared to similar listings. "
        "Return your answer in the following format:\n"
        "Summary: <your compelling summary here>\n"
        "Uniqueness Score: <your uniqueness/rarity score here>"
    )
    
    try:
        response = client.chat.completions.create(
            model="o1-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        raw_output = response.choices[0].message.content.strip()
        print("Raw API output:", raw_output)  # Debug: print the raw API response

        # Use regex to extract the summary and uniqueness score from the multi-line output.
        # The regex is case-insensitive and dot matches newline.
        pattern = r"(?si)summary:\s*(.*?)\s*uniqueness score:\s*(.*)"
        match = re.search(pattern, raw_output)
        if match:
            summary = match.group(1).strip()
            uniqueness_score = match.group(2).strip()
        else:
            summary = "N/A"
            uniqueness_score = "N/A"
        return summary, uniqueness_score
    except Exception as e:
        print("Exception during API call:", e)
        return f"Error generating summary: {e}", "N/A"

def main():
    csv_path = "zillow_properties.csv"
    if not os.path.isfile(csv_path):
        print("Error: zillow_properties.csv not found.")
        sys.exit(1)
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    
    results = []
    
    # Create a header with inline CSS for a Zillow-like clean card layout.
    header = """
<style>
.property-card {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  background-color: #fff;
}
.property-card h2 {
  margin-top: 0;
  font-size: 1.5em;
  color: #2a9d8f;
}
.property-card p {
  margin: 8px 0;
  line-height: 1.5;
  font-family: Arial, sans-serif;
}
.property-card a {
  color: #264653;
  text-decoration: none;
  font-weight: bold;
}
</style>

# Property Listings Analysis
"""
    results.append(header)
    
    # Process each property row from the CSV.
    for index, row in df.iterrows():
        summary, uniqueness_score = generate_summary_for_property(row)
        price = row.get("price", "N/A")
        url = row.get("url", "N/A")
        
        # Format each property as a styled "card" with the listing URL.
        card = f"""
<div class="property-card">
  <h2>Price: ${price}</h2>
  <p><strong>Summary:</strong> {summary}</p>
  <p><strong>Uniqueness Score:</strong> {uniqueness_score}</p>
  <p><a href="{url}" target="_blank">View Listing</a></p>
</div>
"""
        results.append(card)
    
    final_output = "\n".join(results)
    output_path = "_includes/analysis.md"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_output)
        print("Analysis successfully written to", output_path)
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)
    
    # Also print the final output to stdout.
    print(final_output)

if __name__ == "__main__":
    main()
