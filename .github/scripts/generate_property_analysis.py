#!/usr/bin/env python3
import os
import sys
import pandas as pd

try:
    from openai import OpenAI
except ImportError:
    print("Error: The 'openai' library (or your custom O1-mini package) is missing.")
    sys.exit(1)

# Get the OpenAI API key from the environment.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY is missing.")
    sys.exit(1)

# Initialize the OpenAI-like client.
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_summary_for_property(row):
    """
    Given a property row from the CSV, build a prompt and call the OpenAI API
    to generate a 75-word summary and grade. The response is expected in the format:
      Summary: <your summary here>
      Grade: <your grade here>
    This function parses that output and returns (summary, grade).
    """
    price = row.get("price", "N/A")
    url = row.get("url", "N/A")
    last_updated = row.get("last_updated", "N/A")
    beds = row.get("beds", "N/A")
    baths = row.get("baths", "N/A")
    sqft = row.get("sqft", "N/A")
    property_type = row.get("type", "N/A")
    listing_company = row.get("listing_company", "N/A")
    
    prompt = (
        "You are a real estate analyst. Below are details for one property:\n"
        f"Price: {price}\n"
        f"URL: {url}\n"
        f"Last Updated: {last_updated}\n"
        f"Beds: {beds}\n"
        f"Baths: {baths}\n"
        f"Square Feet: {sqft}\n"
        f"Type: {property_type}\n"
        f"Listing Company: {listing_company}\n\n"
        "Generate a concise summary of approximately 75 words describing the property, "
        "highlighting its key features, and assign a grade (for example, 60%, 75%, or 95%) based on its overall appeal and demand for houses of that type. "
        "Return your answer in the following format:\n"
        "Summary: <your summary here>\n"
        "Grade: <your grade here>"
    )
    
    try:
        response = client.chat.completions.create(
            model="o1-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content.strip()
        # Parse the result to separate the summary and grade.
        summary = "N/A"
        grade = "N/A"
        for line in result.splitlines():
            if line.lower().startswith("summary:"):
                summary = line[len("summary:"):].strip()
            elif line.lower().startswith("grade:"):
                grade = line[len("grade:"):].strip()
        return summary, grade
    except Exception as e:
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
    
    # Process each property row.
    for index, row in df.iterrows():
        summary, grade = generate_summary_for_property(row)
        price = row.get("price", "N/A")
        url = row.get("url", "N/A")
        
        # Format each property as a "card" in HTML within markdown.
        card = f"""
<div class="property-card">
  <h2>Price: ${price}</h2>
  <p><strong>Summary:</strong> {summary}</p>
  <p><strong>Grade:</strong> {grade}</p>
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
    
    # Also print to stdout.
    print(final_output)

if __name__ == "__main__":
    main()
