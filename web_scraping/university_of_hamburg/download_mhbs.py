import requests
import json
import urllib.parse
import sys

with open("university_of_hamburg.json", "r") as file:
    data = json.load(file)

for i in data:
    print(urllib.parse.unquote(i[1].split("https://duckduckgo.com/l/?uddg=", 1)[1].split(".pdf&rut=", 1)[0] + ".pdf"))
    sys.exit()