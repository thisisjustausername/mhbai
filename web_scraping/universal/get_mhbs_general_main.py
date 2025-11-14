# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: get the general uni page for each university
# Status: TESTING
# FileID: Sc-ge-0004

# USE THIS FILE TO AUTOMATE THE PROCESS OF FETCHING THE GENERAL MHB PAGE FOR EACH UNIVERSITY
import time
from web_scraping.universal.get_general_mhb_page import automate
from database import database as db

if __name__ == "__main__":
    cursor = db.connect()
    universities = db.select(cursor=cursor, table="universities", keywords=["name", "city"], specific_where="mhb_url IS NOT NULL")
    if universities.is_error:
        db.close(cursor)
        raise universities.error
    universities = universities.data
    while universities != [] and universities is not None:
        try:
            automate()
        except:
            time.sleep(61)
            pass
        universities = db.select(cursor=cursor, table="universities", keywords=["name", "city"], specific_where="mhb_url IS NOT NULL")
        if universities.is_error:
            db.close(cursor)
            raise universities.error
        universities = universities.data
    db.close(cursor)