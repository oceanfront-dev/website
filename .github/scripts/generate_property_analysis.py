#!/usr/bin/env python3
import os
import sys
import pandas as pd
import openai

# Ensure that the OpenAI API key is available
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    sys.exit("Error: OPENAI_API_KEY is not set.")
openai.api_key = OPENAI_API_KEY

def generate_prompt(row):
    """
    Build a prompt using the property metadata.
    Expected CSV columns might include:
      - full_address
      - price
      - beds
      - baths
      - sqft
      - floor_size
      - listing_company
    Adjust field names to match your CSV.
    """
    prompt = (
        f"You are a real estate evaluator. Analyze the following property data and respond in exactly two paragraphs, with no extra commentary.\n\n"
        f"Property Address: {row.get('full_address', 'N/A')}\n"
        f"Price: {row.get('price', 'N/A')}\n"
        f"Bedrooms: {row.get('beds', 'N/A')}, Bathrooms: {row.get('baths', 'N/A')}, Square Feet: {row.get('sqft', 'N/A')}\n"
        f"Floor Size: {row.get('floor_size', 'N/A')}\n"
        f"Listing Company: {row.get('listing_company', 'N/A')}\n\n"
        "Instructions: The first paragraph must consist solely of a property grade (e.g., A, B, C, or a numeric score). The second paragraph must be exactly 50 words long, describing the property’s key features. Use this exact format:\n\n"
        "Grade: <grade>\n"
        "Description: <50-word description>\n"
    )
    return prompt

def generate_analysis(df):
    """
    For each row in the DataFrame, generate analysis using OpenAI.
    Returns a list of strings containing the analysis for each property.
    """
    results = []
    for index, row in df.iterrows():
        prompt = generate_prompt(row)
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7,
            )
            analysis = response.choices[0].message.content.strip()
        except Exception as e:
            analysis = f"Error generating analysis: {e}"
        results.append(f"Property: {row.get('full_address', 'N/A')}\n{analysis}\n")
    return results

def main():
    # Path to the CSV file produced by Workflow 1
    csv_path = "zillow_properties.csv"
    if not os.path.isfile(csv_path):
        sys.exit(f"Error: {csv_path} not found.")
    
    df = pd.read_csv(csv_path)
    
    # (Optional) You might want to filter to only direct results:
    if "is_direct_result" in df.columns:
        df = df[df["is_direct_result"] == True]
    
    analyses = generate_analysis(df)
    output_text = "\n---\n".join(analyses)
    
    # Write the aggregated analysis to a markdown file used by your website.
    output_file = "_includes/analysis.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output_text)
    
    print(f"Analysis generated and saved to {output_file}")

if __name__ == "__main__":
    main()
