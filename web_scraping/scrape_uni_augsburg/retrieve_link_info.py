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


links_dict = dict([i.items() for i in link_info])

links_dict = {key.replace(" ", "%20"): value for key, value in links_dict.items()}

with open("links_information.json", "w") as file:
    json.dump(link_info, file)