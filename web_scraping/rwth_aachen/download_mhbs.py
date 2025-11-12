# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: dowload mhbs from urls and save them as pdfs
# Status: FUNCTIONAL-TEMPORARY
# FileID: Sc-aa-0001

import requests
import json

with open("web_scraping/rwth_aachen/rwth_aachen.json", "r") as file:
    data = json.load(file)

length = len(data)

for index, i in enumerate(data):
    pdf = requests.get(i["url"])
    with open(f"universities/rwth_aachen/{pdf.headers.get('Content-Disposition').split("filename=",1)[1]}", "wb") as file:
        file.write(pdf.content)
    print(f"{index} / {length}")