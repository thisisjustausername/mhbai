# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: create search string for search engine from course information, code works but needs to be polished, use lxml
# Status: IN DEVELOPMENT

from web_scraping.universal.data import database as db
import requests

# connect to db
cursor = db.connect()

# get all universities
query = """SELECT DISTINCT(city, university) FROM universal_mhbs"""
result = db.custom_call(
    cursor=cursor, 
    query=query,
    type_of_answer=db.ANSWER_TYPE.LIST_ANSWER)

if result.is_error:
    print(f"Error fetching universities: {result.error_message}")
    exit(1)

# retrieving data
universities = result.data

# processing data
# TODO: handle error when only one value exists
universities = [i[0].split(',"') if ',"' in i[0] else i[0].split(',') if ',' in i[0] else i[0] for i in universities if len(i) > 0]
universities = [(i[0][1:], i[1][:-2] if i[1].endswith('")') else i[1][:-1]) for i in universities if len(i) == 2]
universities = [{"university": i[1], "city": i[0]} for i in universities]

# mapping
# abbreviations = {"TU": "Technische Hochschule", "FH": "Fachhochschule", "HS": "Hochschule", "OTH": "Ostbayerische Technische Hochschule", "THWS": "Technische Hochschule Würzburg-Schweinfurt"}

# create search strings
for uni in universities:
    # get university url
    base_url = "https://www.google.com/search?q="
    search_string = f"{base_url}{uni['university'].replace(' ', '+')}+{uni['city'].replace(' ', '+')}+website"
    uni["search_string"] = search_string

print(universities)
