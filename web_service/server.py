# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

from flask import Flask, render_template, request, jsonify
from pdf_reader import pdf_reader_toc as prt
from pdf_reader.MHB_Overlaps import Overlaps
import os
import numpy as np
import json

app = Flask(__name__)

with open("web_scraping/scrape_uni_augsburg/links_information.json", "r") as file:
    links_data =  json.load(file)

@app.route("/")
def home():
    """
    home \n
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
            module_data = dict((i[0], i[1]) if i[1] != None else (i[0], no_infos) for i in module_data.items())
        except:
            module_data = {"title": no_infos,
                           "module_code": i,
                           "ects": no_infos,
                           "content": no_infos,
                           "goals": no_infos}
        information_overlaps.append(module_data)

    return jsonify({"data": information_overlaps})


@app.route("/compare", methods=["POST"])
def compare_simple():
    """compare_simple \n
    compares two mhbs"""

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
    overlaps = Overlaps.input_paths(["pdfs/" + i for i in file_names])

    return jsonify({"data": overlaps.ovl_modules})

def get_file_name(url: str) -> str:
    """
    get_file_name \n
    gets the file name that fits to the url
    :param url: url \n
    :type url: str
    :return: file name or link if no file name was found\n
    :rtype: str
    """
    if url not in links_data.keys():
        return url.split("/")[-1]
    return links_data[url]

@app.route("/export", methods=["POST"])
def export():
    """def export \n
    exports the data in a wished format and with or without detailed information"""
    data_type = request.args.get("dataType")
    data_list = request.args.get("dataList")
    data_list = data_list.split(",") if data_list is not None else None

    allowed_data_types = ["json", "xlsx", "txt", "pdf", "csv"]



if __name__ == "__main__":
    app.run(debug=True)