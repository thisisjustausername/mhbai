# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: get url of uni page for each university, but automated with rate limit handling
# Status: VERSION 1.0
# FileID: Sc-ge-0003

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