#!/usr/bin/env python3
"""
Auto-Scraper Cron - Runs once daily on weekdays at random time
Schedule: Daily at 5:00 AM, then waits random 30-32.5 hours, scrapes once
"""
import os
import sys
import time
import random
import schedule
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from multi_region_scraper import scrape_all_regions
from subscription_manager import (
    get_active_subscribers, filter_new_permits, save_fresh_dump,
    cleanup_old_seen_permits, save_to_archive
)
from email_service import send_permit_email
import json


# ==================== SCRAPER LOOP ====================

def scrape_and_feed():
    """Main scraping loop - runs once daily on weekdays at random time"""
    print("\n" + "="*70)
    print(f"🤖 AUTO-SCRAPER RUNNING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Check if weekend - exit if Saturday (5) or Sunday (6)
    if datetime.now().weekday() in [5, 6]:
        print("   📅 Weekend detected - skipping scrape")
        return
    
    # Calculate random wait time: 1800-1950 minutes past 5 AM
    wait_time = random.randint(1800, 1950)
    start_time = datetime.now().replace(hour=5, minute=0, second=0, microsecond=0) + timedelta(minutes=wait_time)
    
    print(f"   ⏰ Random scrape time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Wait until start time
    while datetime.now() < start_time:
        time.sleep(60)  # Sleep 1 minute
    
    print(f"   🚀 Starting scrape at {datetime.now().strftime('%H:%M:%S')}")
    
    # Get all active subscribers grouped by city
    subscribers = get_active_subscribers()
    
    if not subscribers:
        print("   ⚠️  No active subscribers")
        return
    
    # Group by city
    cities_to_scrape = {}
    for sub in subscribers:
        user_id, email, city = sub[1], sub[2], sub[3]
        
        if city not in cities_to_scrape:
            cities_to_scrape[city] = []
        
        cities_to_scrape[city].append({
            'user_id': user_id,
            'email': email
        })
    
    print(f"\n📍 Cities to scrape: {len(cities_to_scrape)}")
    for city, users in cities_to_scrape.items():
        print(f"   • {city}: {len(users)} subscribers")
    
    # Scrape each city
    for city, users in cities_to_scrape.items():
        try:
            print(f"\n🕷️  Scraping {city}...")
            
            # Map city name to metro
            metro = city.split('-')[0]  # e.g., "Nashville-Davidson" → "Nashville"
            
            # Scrape the city
            all_permits = scrape_all_regions([metro])
            
            if not all_permits:
                print(f"   ⚠️  No permits found for {city}")
                continue
            
            # Filter for this specific city/county
            city_permits = [p for p in all_permits if f"{p.get('metro', '')}-{p.get('county', '')}" == city]
            
            if not city_permits:
                print(f"   ⚠️  No permits found for {city}")
                continue
            
            print(f"   ✅ Scraped {len(city_permits)} total permits")
            
            # Filter NEW permits (not seen before)
            new_permits = filter_new_permits(city, city_permits)
            
            if not new_permits:
                print(f"   ℹ️  No new permits (all duplicates)")
                continue
            
            print(f"   🆕 Found {len(new_permits)} NEW permits!")
            
            # Feed to each subscriber
            for user in users:
                user_id = user['user_id']
                email = user['email']
                
                try:
                    # Save fresh dump
                    csv_file = save_fresh_dump(city, user_id, new_permits)
                    
                    if csv_file:
                        # Send email
                        send_permit_email(
                            to_email=email,
                            city=city,
                            permit_count=len(new_permits),
                            csv_file=csv_file
                        )
                        
                        print(f"   📧 Sent to {email}")
                
                except Exception as e:
                    print(f"   ❌ Error feeding {email}: {e}")
        
        except Exception as e:
            print(f"   ❌ Error scraping {city}: {e}")
    
    # Cleanup old seen permits (keep 30 days)
    deleted = cleanup_old_seen_permits(days=30)
    if deleted > 0:
        print(f"\n🧹 Cleaned up {deleted} old permit records")
    
    print("\n" + "="*70)
    print("✅ Scraping complete!")
    print("="*70)


# ==================== SCHEDULE SETUP ====================

def setup_schedule():
    """Set up daily scraping schedule at 5:00 AM"""
    
    # Schedule scraping once per day at 5:00 AM
    schedule.every().day.at("05:00").do(scrape_and_feed)
    
    print("="*70)
    print("⏰ AUTO-SCRAPER SCHEDULE")
    print("="*70)
    print("   • 5:00 AM  - Daily start (weekdays only)")
    print("   • Random wait: 30-32.5 hours")
    print("   • Actual scrape: ~11:00 AM - 1:30 PM")
    print("="*70)
    print("\n🤖 Scraper is running... (Press Ctrl+C to stop)")
    print()


def run_once():
    """Run scraper once immediately (for testing)"""
    print("🧪 Running scraper ONCE (test mode)...\n")
    scrape_and_feed()


# ==================== MAIN ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-scraper cron system')
    parser.add_argument('--once', action='store_true', help='Run scraper once and exit')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon (daily on weekdays)')
    
    args = parser.parse_args()
    
    if args.once:
        # Test mode - run once
        run_once()
    
    elif args.daemon:
        # Daemon mode - run on schedule
        setup_schedule()
        
        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n\n👋 Auto-scraper stopped")
    
    else:
        print("Usage:")
        print("  python3 auto_scraper_cron.py --once     # Run once (test)")
        print("  python3 auto_scraper_cron.py --daemon   # Run as daemon (daily weekdays)")
