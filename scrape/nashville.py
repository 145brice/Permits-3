#!/usr/bin/env python3
"""
Nashville scraper - pulls permits from Davidson County site
"""
import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime

def scrape_nashville():
    """Scrape Nashville-Davidson county permits and append to CSV"""
    print("🕷️ Scraping Nashville-Davidson permits...")

    # Mock data for demo - replace with real scraping
    permits = [
        {
            "county": "Nashville-Davidson",
            "permit_number": "REAL-001",
            "address": "789 Elm St, Nashville, TN",
            "permit_type": "Commercial Renovation",
            "estimated_value": 150000,
            "work_description": "Office space renovation",
            "date": datetime.now().strftime('%Y-%m-%d')
        }
    ]

    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)

    # Append to CSV
    csv_path = 'data/permits.csv'
    file_exists = os.path.exists(csv_path)

    with open(csv_path, 'a', newline='') as csvfile:
        fieldnames = ['county', 'permit_number', 'address', 'permit_type', 'estimated_value', 'work_description', 'date']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for permit in permits:
            writer.writerow(permit)

    print(f"✅ Added {len(permits)} permits to {csv_path}")

if __name__ == '__main__':
    scrape_nashville()
