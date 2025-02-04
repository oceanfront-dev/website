#!/usr/bin/env python3

import os
import re
import sys

try:
    from openai import OpenAI
except ImportError:
    print("Error: The 'openai' library (or your custom O1-mini package) is missing.")
    sys.exit(1)

# We assume you set OPENAI_API_KEY in your GitHub Actions environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Regex to detect lines like "New Record #104236 Title: Endocast [Mesh] [CT]"
RE_RECORD_HEADER = re.compile(r'^New Record #(\d+)\s+Title:\s*(.*)$', re.IGNORECASE)

def parse_records_from_body(body: str):
    """
    Parses the release body, looking for lines like:
      New Record #XXXX Title: ...
    Then captures subsequent lines of the form 'Key: Value', e.g.:
      Detail Page URL: ...
      Object: ...
      Taxonomy: ...
      etc.

    Returns a list of dicts, each representing a record's data:
      {
        "record_number": "104236",
        "title": "Endocast [Mesh] [CT]",
        "detail_url": "...",
        "Object": "...",
        "Taxonomy": "...",
        ...
      }
    """
    records = []
    lines = body.splitlines()
    current_record = {}

    for line in lines:
        line = line.strip()
        # Skip empty lines
        if not line:
            continue

        # See if this line starts a new record
        match = RE_RECORD_HEADER.match(line)
        if match:
            # If we already have a record in progress, finalize it
            if current_record:
                records.append(current_record)
            current_record = {}
            current_record["record_number"] = match.group(1)
            current_record["title"] = match.group(2)
            continue

        # Otherwise, if line looks like "SomeKey: SomeValue"
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip()
            val = parts[1].strip()
            kl = key.lower()

            # We can store known fields in canonical keys
            if kl.startswith("detail page url"):
                current_record["detail_url"] = val
            elif kl == "object":
                current_record["Object"] = val
            elif kl == "taxonomy":
                current_record["Taxonomy"] = val
            elif kl == "element or part":
                current_record["Element or Part"] = val
            elif kl == "data manager":
                current_record["Data Manager"] = val
            elif kl == "date uploaded":
                current_record["Date Uploaded"] = val
            elif kl == "publication status":
                current_record["Publication Status"] = val
            elif kl == "rights statement":
                current_record["Rights Statement"] = val
            elif kl == "cc license":
                current_record["CC License"] = val

            # Also store the raw key-value in case we need it
            current_record[key] = val

    # After the loop, if there's a record in progress, append it
    if current_record:
        records.append(current_record)

    return records

def generate_text_for_records(records):
    """
    Calls the o1-mini model (via OpenAI-like usage) to generate a multi-paragraph,
    ~200-word description for each record, focusing on species/taxonomy and object details.
    """
    if not OPENAI_API_KEY:
        return "Error: OPENAI_API_KEY is missing."

    # Initialize the client
    client = OpenAI(api_key=OPENAI_API_KEY)

    # If no records found, bail out
    if not records:
        return "No new records to summarize."

    # Build a user prompt that includes each record's metadata
    user_content = ["Below are new CT records from a MorphoSource release:\n"]
    for rec in records:
        record_num = rec.get("record_number", "N/A")
        user_content.append(f"Record #{record_num}:")
        user_content.append(f" - Title: {rec.get('title','N/A')}")
        user_content.append(f" - URL: {rec.get('detail_url','N/A')}")

        for field in [
            "Object",
            "Taxonomy",
            "Element or Part",
            "Data Manager",
            "Date Uploaded",
            "Publication Status",
            "Rights Statement",
            "CC License",
        ]:
            if field in rec:
                user_content.append(f" - {field}: {rec[field]}")
        user_content.append("")  # Blank line separator

    # Add instructions for a ~200-word multi-paragraph summary
    user_content.append(
        "You are a scientific writer with expertise in analyzing morphological data. "
        "You have received metadata from X-ray computed tomography scans of various biological specimens. "
        "Please compose a multi-paragraph, one for each record/species, ~200-word plain-English description that "
        "emphasizes each specimen’s species (taxonomy) and object details. Focus on identifying notable anatomical "
        "or morphological features that may be revealed by the CT scanning process. Avoid discussions of copyright "
        "or publication status. Make the final description readable for a broad audience, yet scientifically informed. "
        "Highlight the significance of the scans for understanding the organism’s structure and potential insights "
        "into its biology or evolution."
    )

    try:
        resp = client.chat.completions.create(
            model="o1-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "\n".join(user_content)
                        }
                    ]
                }
            ]
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Error calling o1-mini model: {e}"

def main():
    """
    1. Reads a single argument <release_body_file>
    2. Parses it for "New Record #..." blocks
    3. Calls generate_text_for_records(records) to produce a multi-paragraph text
    4. Prints the final text to stdout
    """
    if len(sys.argv) < 2:
        print("Usage: generate_property_analysis.py <release_body_file>")
        sys.exit(1)

    release_body_file = sys.argv[1]
    if not os.path.isfile(release_body_file):
        print(f"File '{release_body_file}' not found.")
        sys.exit(1)

    with open(release_body_file, "r", encoding="utf-8") as f:
        body = f.read()

    # Parse records
    records = parse_records_from_body(body)
    # Generate final text using the o1-mini model
    description = generate_text_for_records(records)
    print(description)

if __name__ == "__main__":
    main()
