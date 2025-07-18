import json
import requests
import re
import zlib

with open("../../../web_scraping/scrape_uni_augsburg/uni_a_all_mhbs.json", "r") as file:
    data = json.load(file)

pdf = requests.get(data[0]).content
pdf_readable = requests.get(data[1]).text

print(data[0])

start_xref = int(list(re.finditer(rb'startxref\s+(\d+)', pdf))[-1].group(1))
xref_data = pdf[start_xref:]

assert xref_data.startswith(b'xref')

xref_header_match = re.match(rb'xref\s+(\d+)\s+(\d+)', xref_data)

assert xref_header_match is not None

# start object
start_obj = int(xref_header_match.group(1))

# number of elements
count = int(xref_header_match.group(2))

# end
header_end = xref_header_match.end()

# body
xref_body = xref_data[header_end:]

xref_entries = []
for i in range(count):
    entry = xref_body[i * 20:(i + 1) * 20].strip(b'\n')
    #print(entry)
    if len(entry) < 18:
        #print("invalid")
        continue  # skip invalid/incomplete lines

    offset = int(entry[0:10])
    generation = int(entry[11:16])
    in_use = entry[17:18].decode('ascii')
    """offset = int(entry[0:10])
    generation = int(entry[11:16])
    in_use = entry[17:18].decode()"""
    xref_entries.append({
        'obj_num': start_obj + i,
        'offset': offset,
        'generation': generation,
        'in_use': in_use
    })

def replace_heading(match):
    return match.group(0) + rb' __heading__'

#print(xref_entries)

for i in xref_entries:
    obj_offset = i['offset']
    next_100k = pdf[obj_offset:obj_offset + 100000]  # read ahead

    # Find the `endobj` marker
    end_index = next_100k.find(b'endobj')
    if end_index == -1:
        raise ValueError("endobj not found")

    object_data = next_100k[:end_index + len(b'endobj')]

    stream_match = re.search(rb'stream\s*[\r\n]+(.*?)endstream', object_data, re.DOTALL)
    if stream_match:
        stream_raw = stream_match.group(1)
        try:
            stream_decoded = zlib.decompress(stream_raw)
            # replace the dots in the table of contents with a single comment _page_number_\n
            stream_decoded = re.sub(rb'1 0 0 -1 \d+\.\d+ \d+\.\d+ Tm \[\(\.\)\] TJ\n', b'_np_', stream_decoded)
            stream_decoded = re.sub(rb'(_np_)+', rb'__page_number__\n', stream_decoded)

            # mark headings with size 9
            # stream_decoded = re.sub(rb'/F\d+ \d+\.\d+|\d+ Tf', replace_heading, stream_decoded)
            stream_decoded = re.sub(rb'/F3 9 Tf', replace_heading, stream_decoded)
            #print("\n[Decoded Flate stream content:]")
            print(stream_decoded.decode('latin1', errors='ignore'))  # Use utf-8 if sure it's text
            print("new page--------------------------------new page--------------------------------new page")
        except Exception as e:
            print(f"[Decompression failed] {e}")

# hardcoded extracting the trailer
objects = re.findall(rb'(\d+)\s+(\d+)\s+obj(.*?)endobj', pdf, re.DOTALL)[-9:]
trailer = b''.join([i[2] for i in objects])

# to create the object part_pdf1.txt simply get a one page content by "\n\nq\n" splitting there