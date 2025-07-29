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