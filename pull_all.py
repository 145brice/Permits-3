#!/usr/bin/env python3
"""
Master scraper - runs all city scrapers
"""
import os
import sys
import importlib.util

def run_all_scrapers():
    """Import and run all scrapers in the scrape/ directory"""
    scrape_dir = 'scrape'

    if not os.path.exists(scrape_dir):
        print(f"❌ {scrape_dir} directory not found")
        return

    # Find all .py files in scrape/
    scraper_files = [f for f in os.listdir(scrape_dir) if f.endswith('.py')]

    for scraper_file in scraper_files:
        module_name = scraper_file[:-3]  # remove .py
        module_path = os.path.join(scrape_dir, scraper_file)

        print(f"🚀 Running {module_name}...")

        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Call the scrape function (assuming it's named scrape_<city>)
            scrape_func = getattr(module, f'scrape_{module_name}', None)
            if scrape_func:
                scrape_func()
            else:
                print(f"❌ No scrape_{module_name} function found in {scraper_file}")

        except Exception as e:
            print(f"❌ Error running {scraper_file}: {e}")

if __name__ == '__main__':
    run_all_scrapers()
