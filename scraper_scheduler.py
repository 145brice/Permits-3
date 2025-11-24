import random
import time
import datetime
import subprocess

# Set CST offset from UTC (CST is UTC-6, no DST handling here)
CST_OFFSET = -6

# Define the time window in CST
START_HOUR = 5
END_HOUR = 5
START_MINUTE = 0
END_MINUTE = 30

# Get today's date in UTC
now_utc = datetime.datetime.utcnow()
# Calculate today's 5:00am and 5:30am CST in UTC
start_cst = now_utc.replace(hour=START_HOUR - CST_OFFSET, minute=START_MINUTE, second=0, microsecond=0)
end_cst = now_utc.replace(hour=END_HOUR - CST_OFFSET, minute=END_MINUTE, second=0, microsecond=0)

# If we've already passed the window for today, schedule for tomorrow
if now_utc > end_cst:
    start_cst += datetime.timedelta(days=1)
    end_cst += datetime.timedelta(days=1)

# Pick a random time between start_cst and end_cst
window_seconds = int((end_cst - start_cst).total_seconds())
random_offset = random.randint(0, window_seconds)
scheduled_time = start_cst + datetime.timedelta(seconds=random_offset)

# Sleep until the scheduled time
sleep_seconds = (scheduled_time - now_utc).total_seconds()
print(f"[scraper_scheduler] Sleeping for {int(sleep_seconds)} seconds until {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')} UTC (random time between 5:00-5:30am CST)")
time.sleep(max(0, sleep_seconds))

# Run the scraper (replace 'python scraper.py' with your actual scraper command)
print("[scraper_scheduler] Running scraper now...")
subprocess.run(["python3", "scraper.py"])