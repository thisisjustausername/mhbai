# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: Unspecified
# Status: IN DEVELOPMENT
# FileID: -

import json
from pdf_reader.MHB import MHB

import traceback

with open("uni_augsburg_error_files.json", "r") as file:
    data = json.load(file)

with open("web_scraping/scrape_uni_augsburg/links_information.json", "r") as file:
    links_data =  json.load(file)

look_up = [(k, v) for k, v in links_data.items()]

for i in data:
    # print(next(k for k, v in look_up if v == i))
    try:
        MHB("pdfs/" + i)
        print("SUCCESS")
    except Exception as e:
        # traceback.print_exc()
        print("ERROR")        