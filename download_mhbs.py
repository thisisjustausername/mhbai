import requests
import json

# get all the Modulhandbuch-urls, that were scraped from the website of the University of Augsburg
with open("uni_a_all_mhbs.json", "r") as file:
    data = json.load(file)

for index, url in enumerate(data):
    print(f"{index + 1}/{len(data)}")
    print(url)
    pdf = requests.get(url)
    # save each pdf under the exact same name
    with open(f"pdfs/{pdf.headers.get('Content-Disposition').split('filename=', 1)[1]}", "wb") as file:
        file.write(pdf.content)