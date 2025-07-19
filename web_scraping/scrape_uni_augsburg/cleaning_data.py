import os
import json

with open("pdf_data.json", "r") as file:
    data = json.load(file)

print(len(data))

def flatten_dict(dictionary: dict) -> tuple:
    listing = []
    for i in dictionary.items():
        value = i[1] if not isinstance(i[1], list) else tuple(i[1])
        pair = (i[0], value)
        listing.append(pair)
    return tuple(listing)

cleaned_data = [flatten_dict(i) for i in data]
print(cleaned_data)
cleaned_data = list(set(cleaned_data))
print(len(cleaned_data))

