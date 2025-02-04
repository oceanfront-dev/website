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
    Given a pandas Series (a property row from the CSV), builds a prompt
    and calls the OpenAI API to generate a 75-word summary and grade.
    """
    # Use N/A for missing values.
    price = row.get("price", "N/A")
    url = row.get("url", "N/A")
    last_updated = row.get("last_updated", "N/A")
    beds = row.get("beds", "N/A")
    baths = row.get("baths", "N/A")
    sqft = row.get("sqft", "N/A")
    property_type = row.get("type", "N/A")
    listing_company = row.get("listing_company", "N/A")
    
    # Build the prompt.
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
        "highlighting its key features, and assign a grade (for example, 95%, 75%, or 85%) based on its overall appeal, price, and location of the listing. "
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
        return result
    except Exception as e:
        return f"Error generating summary: {e}"

def main():
    # Verify that the CSV file exists.
    csv_path = "zillow_properties.csv"
    if not os.path.isfile(csv_path):
        print("Error: zillow_properties.csv not found.")
        sys.exit(1)
    
    # Read the CSV into a pandas DataFrame.
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    
    # Build summaries for each property.
    results = []
    for index, row in df.iterrows():
        summary = generate_summary_for_property(row)
        # You can include an identifier for each property if desired.
        results.append(f"Property {index + 1}:\n{summary}\n")
    
    # Combine all summaries.
    final_output = "\n".join(results)
    
    # Write the final output to a file (which your workflow will commit and release).
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
