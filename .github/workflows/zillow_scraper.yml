name: Scrape Zillow Listings

on:
  schedule:
    - cron: "0 0 * * *"  # Runs every 24 hours at midnight UTC; adjust as needed
  workflow_dispatch:

permissions:
  contents: write

jobs:
  scrape_and_release:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v3
        with:
          persist-credentials: true

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.9"

      - name: Install dependencies
        run: pip install requests beautifulsoup4 lxml

      - name: Run Zillow Scraper
        id: scraper
        run: python .github/scripts/scrape_zillow.py

      - name: Commit updated last_count.txt
        if: steps.scraper.outputs.new_data == 'true'
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add .github/last_count.txt
          git commit -m "Update last_count.txt for new Zillow listings"
          git push

      - name: Generate Timestamp
        id: gen_ts
        if: steps.scraper.outputs.new_data == 'true'
        run: |
          TS=$(date +'%Y-%m-%d_%H-%M-%S')
          echo "timestamp=$TS" >> $GITHUB_OUTPUT

      - name: Create or Update Release
        if: steps.scraper.outputs.new_data == 'true'
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: zillow-updates-${{ steps.gen_ts.outputs.timestamp }}
          release_name: "Zillow Updates #${{ steps.gen_ts.outputs.timestamp }}"
          body: ${{ steps.scraper.outputs.details }}
          draft: false
          prerelease: false
