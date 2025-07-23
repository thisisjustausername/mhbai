import requests
import json

with open("uni_a_all_mhbs.json", "r") as file:
    data = json.load(file)

link_info = []
error_links = []
for index, i in enumerate(data):
    try:
        link_info.append({i: requests.get(i).headers["Content-Disposition"].split("attachment; filename=", 1)[1]})
    except:
        print(f"Error occured in {i}")
        error_links.append(i)

with open("links_information.json", "w") as file:
    json.dump(link_info, file)