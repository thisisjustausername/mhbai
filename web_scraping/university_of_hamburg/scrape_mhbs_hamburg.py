# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

import requests
from bs4 import BeautifulSoup
import json

# get all courses of study
with open("web_scraping/university_of_hamburg/table_data_all_courses.txt", "r") as file:
    result = file.read()
soup = BeautifulSoup(result, 'lxml')
data = soup.find_all("tr")
print(len(data))
info_list = []
for i in data:
    information = i.find("td")
    url = "https://www.uni-hamburg.de/campuscenter/" + information.find("a").get("href")
    text = information.get_text()
    info_list.append((text, url))

data = list(set(info_list))
data = [{"name": i[0], "url": i[1]} for i in data]

with open("web_scraping/university_of_hamburg/courses_of_study.json", "w") as file:
    json.dump(data, file)