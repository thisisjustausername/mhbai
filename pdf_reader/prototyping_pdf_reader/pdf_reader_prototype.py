# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai and pdf_reader.
#
# For usage please contact the developer.

# Description: Tests extracting data from MHBs from University of Augsburg
# Status: PROTOTYPING
# FileID: Re-te-0003

import re
import zlib
import requests
import json

with open("../../../web_scraping/scrape_uni_augsburg/uni_a_all_mhbs.json", "r") as file:
    urls = json.load(file)

new_data = requests.get(urls[0]).content

# Match compressed stream objects
pattern = re.compile(
    rb"(\d+)\s+(\d+)\s+obj\s+<<(.*?)>>\s+stream\s+(.*?)\s+endstream",
    re.DOTALL,
)
matches = pattern.findall(new_data)

stringer = ""
for obj_num, gen_num, raw_dict, stream_data in matches:
    if b"/FlateDecode" in raw_dict:
        try:
            decoded = zlib.decompress(stream_data.strip())
            print(f"Decoded stream from object {obj_num.decode()}:\n")
            stringer += ("\n" + decoded.decode(errors="replace"))  # interpret as text
        except Exception as e:
            print(f"Error decompressing object {obj_num.decode()}: {e}")

stringer = stringer.split("\n", 1)[1]
lines = stringer.split("\n")
in_text_block = False
for line in lines:
    if "BT" in line:
        in_text_block = True
    elif "ET" in line:
        in_text_block = False
    elif in_text_block and "TJ" in line:
        match = re.search(r"\[(\(.*?)\)]\s*TJ", line)
        if match:
            print("Text:", match.group(1))