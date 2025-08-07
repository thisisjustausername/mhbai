# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

from typing import List
from flask import Flask, render_template, request, jsonify, session, Response
from pdf_reader import pdf_reader_toc as prt
from pdf_reader.MHB_Overlaps import Overlaps
from pdf_reader.MHB import MHB
import os
import numpy as np
import json
from itertools import groupby
app = Flask(__name__)

global overlaps
global mhb_data

with open("web_service/uni_augsburg_look_up.json", "r") as file:
    mhb_data = json.load(file)


with open("web_scraping/scrape_uni_augsburg/links_information.json", "r") as file:
    links_data =  json.load(file)

@app.route("/")
def home():
    """
    creates the homepage
    """
    return render_template("home.html")

@app.route("/compareFast", methods=["POST"])
def compareFast():
    data = request.get_json()
    file_name_1 = data.get('mhb1')
    file_name_2 = data.get('mhb2')

    file_names = [file_name_1, file_name_2]

    # allows to input either filenames (with or without .pdf at the end) or urls
    file_names = [get_file_name(i) if "/" in i else i for i in file_names]
    file_names = [i + ".pdf" if not ".pdf" in i else i for i in file_names]
    if any([False if i in os.listdir("pdfs") else True for i in file_names]):
        Exception("No valid pdf files")

    # mhbs = [MHB("pdfs/" + i) for i in file_names]
    modules = [prt.Modules("pdfs/" + i) for i in file_names]
    #print(modules[0])
    no_infos = "k.A."

    extracted_modules = [i.toc_module_codes() for i in modules]
    # do not sort in order to keep it cleaner for the user
    # sort in order to save operations in the next step
    # extracted_modules.sort(key=lambda x: len(x))
    overlaps_out_of_order = set(extracted_modules[0]).intersection(*extracted_modules[1:])

    min_list = extracted_modules[np.argmin([len(i) for i in extracted_modules])]
    overlapping_modules = [i for i in min_list if i in overlaps_out_of_order]
    # overlapping_modules = list(set(extracted_modules[0]).intersection(*extracted_modules[1:]))

    information_overlaps = []
    for i in overlapping_modules:
        try:
            module_data = modules[0].data_to_module(i)
            module_data = dict((i[0], i[1]) if i[1] != None else (i[0], no_infos) for i in module_data.items()) #type: ignore[OptionalMemberAccess]
        except:
            module_data = {"title": no_infos,
                           "module_code": i,
                           "ects": no_infos,
                           "content": no_infos,
                           "goals": no_infos}
        information_overlaps.append(module_data)

    return jsonify({"data": information_overlaps})

# NOTE doesn't work when duplicate pages exist
def group_pages(pages: List[int]) -> str:
    grouped_pages = []
    pages.sort()
    for _, g in groupby(pages, key=lambda x: x - pages.index(x)):
        group = list(g)
        grouped_pages.append(f"{group[0]} - {group[-1]}" if len(group) > 1 else str(group[0]))
    return ", ".join(grouped_pages)

@app.route("/compareEfficient", methods=["POST"])
def compare_efficient():
    global overlaps
    global mhb_data

    data = request.get_json()
    file_name_1 = data.get('mhb1')
    file_name_2 = data.get('mhb2')

    file_names = [file_name_1, file_name_2]

    # allows to input either filenames (with or without .pdf at the end) or urls
    file_names = [get_file_name(i) if "/" in i else i for i in file_names]
    file_names = [i + ".pdf" if not ".pdf" in i else i for i in file_names]
    if any([False if i in os.listdir("pdfs") else True for i in file_names]):
        Exception("No valid pdf files")

    if len(set(file_names)) == 1:
        mhb = mhb_data[file_names[0]]
        overlaps = MHB.init_manually(path=file_names[0], title=mhb["title"], name=mhb["name"], module_codes=mhb["module_codes"], modules=mhb["modules"])
        print()
        ovl_modules = overlaps.modules
        ovl_modules = [{k: v if k != "pages" else group_pages(v) for k, v in i.items()} for i in ovl_modules]
    else:
        mhbs = [mhb_data[i] for i in file_names]
        overlaps = Overlaps([MHB.init_manually(path=i, title=i["title"], name=i["name"], module_codes=i["module_codes"], modules=i["modules"]) for i in mhbs])
        ovl_modules = overlaps.ovl_modules
    return jsonify({"data": ovl_modules})


# TODO when both links / pdfs are identical don't do Overlaps but MHB and don't display Überschneidungen but Informationen
@app.route("/compare", methods=["POST"])
def compare_simple():
    global overlaps
    """
    compares two mhbs
    """

    data = request.get_json()
    file_name_1 = data.get('mhb1')
    file_name_2 = data.get('mhb2')

    file_names = [file_name_1, file_name_2]

    # allows to input either filenames (with or without .pdf at the end) or urls
    file_names = [get_file_name(i) if "/" in i else i for i in file_names]
    file_names = [i + ".pdf" if not ".pdf" in i else i for i in file_names]
    if any([False if i in os.listdir("pdfs") else True for i in file_names]):
        Exception("No valid pdf files")
    """
    # mhbs = [MHB("pdfs/" + i) for i in file_names]
    modules = [prt.Modules("pdfs/" + i) for i in file_names]
    #print(modules[0])
    no_infos = "k.A."

    extracted_modules = [i.toc_module_codes() for i in modules]
    # do not sort in order to keep it cleaner for the user
    # sort in order to save operations in the next step
    # extracted_modules.sort(key=lambda x: len(x))
    overlaps_out_of_order = set(extracted_modules[0]).intersection(*extracted_modules[1:])

    min_list = extracted_modules[np.argmin([len(i) for i in extracted_modules])]
    overlapping_modules = [i for i in min_list if i in overlaps_out_of_order]
    # overlapping_modules = list(set(extracted_modules[0]).intersection(*extracted_modules[1:]))

    information_overlaps = []
    for i in overlapping_modules:
        try:
            module_data = modules[0].data_to_module(i)
            module_data = dict((i[0], i[1]) if i[1] != None else (i[0], no_infos) for i in module_data.items())
        except:
            module_data = {"title": no_infos,
                           "module_code": i,
                           "ects": no_infos,
                           "content": no_infos,
                           "goals": no_infos}
        information_overlaps.append(module_data)"""

    if len(set(file_names)) == 1:
        overlaps = MHB("pdfs/" + file_names[0])
        ovl_modules = overlaps.modules
        ovl_modules = [{k: v if k != "pages" else group_pages(v) for k, v in i.items()} for i in ovl_modules]
    else:
        overlaps = Overlaps.input_paths(["pdfs/" + i for i in file_names])
        ovl_modules = overlaps.ovl_modules
    return jsonify({"data": ovl_modules})

def get_file_name(url: str) -> str:
    """
    gets the file name that fits to the url

    Parameters:
        url (str): url \n
    Returns:
    str: file name or link if no file name was found\n
    """
    if url not in links_data.keys():
        return url.split("/")[-1]
    return links_data[url]

@app.route("/export", methods=["GET"])
def export():
    """
    exports the data in a wished format and with or without detailed information
    """
    
    """data_type = request.args.get("dataType")
    data_list = request.args.get("dataList")
    data_list = data_list.split(",") if data_list is not None else None
    allowed_data_types = ["json", "xlsx", "txt", "pdf", "csv"]
    """
    global overlaps
    if isinstance(overlaps, Overlaps):
        name = "__".join([i.name for i in overlaps.mhbs])
    else:
        name = overlaps.name
    return Response(overlaps.export(file_type="html", borders=True).getvalue(), #type: ignore[OptionalMemberAccess]
                    headers={"Content-Disposition": f"attachment; filename={name}.html"})
    # return name, overlaps.export(file_type="html")

if __name__ == "__main__":
    app.run(debug=True)