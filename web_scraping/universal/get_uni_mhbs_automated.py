import time
from datetime import datetime, timedelta

from web_scraping.universal.get_mhb_studieren import main as get_mhbs

retry = True

while retry:
    try:
        get_mhbs()
        retry = False
    except Exception as e:
        if "Rate limit exceeded" in str(e):
            print(f"Rate limit exceeded. Retrying in 10 minutes at {(datetime.now() + timedelta(minutes=10)).strftime('%H:%M:%S')}")
            time.sleep(10 * 60)
        else:
            print(f"An unexpected error occurred: {e}")
            retry = False