# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai and pdf_reader.
#
# For usage please contact the developer.

# Description: Tests functions for extracting text from PDF streams
# Status: PROTOTYPING
# FileID: Re-te-0001

import re
import zlib
import json
import requests

def find_objects_with_streams(pdf_bytes):
    object_pattern = re.compile(rb'(\d+)\s+(\d+)\s+obj(.*?)endobj', re.DOTALL)
    for match in object_pattern.finditer(pdf_bytes):
        obj_num = int(match.group(1))
        obj_gen = int(match.group(2))
        obj_data = match.group(3)
        if b'stream' in obj_data:
            yield obj_num, obj_gen, obj_data

def extract_stream_data(obj_data):
    # Find stream boundaries
    stream_match = re.search(rb'stream\r?\n(.*?)\r?\nendstream', obj_data, re.DOTALL)
    if not stream_match:
        return None
    stream = stream_match.group(1)
    # Check for compression
    if b'/FlateDecode' in obj_data:
        try:
            stream = zlib.decompress(stream)
        except Exception as e:
            print("Decompression error:", e)
            return None
    return stream

def extract_text_from_stream(stream):
    # Find all text between BT...ET
    bt_et_blocks = re.findall(rb'BT(.*?)ET', stream, re.DOTALL)
    lines = []
    for block in bt_et_blocks:
        # Find all text items in parentheses
        texts = re.findall(rb'\((.*?)\)', block)
        for t in texts:
            try:
                lines.append(t.decode('utf-8', errors='replace'))
            except:
                lines.append(str(t))
    return lines

# Usage:
# pdf_bytes = ... (read from file, download, etc.)

with open("../../../web_scraping/scrape_uni_augsburg/uni_a_all_mhbs.json", "r") as file:
    data = json.load(file)

pdf = requests.get(data[0]).content

for obj_num, obj_gen, obj_data in find_objects_with_streams(pdf):
    stream = extract_stream_data(obj_data)
    if stream:
        lines = extract_text_from_stream(stream)
        for line in lines:
            print(f"{obj_num} {obj_gen}:", line)