# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

from flask import Flask, session, g, flash, render_template, request, redirect, url_for, make_response, jsonify
import backend.pdf_reader_toc as prt
import os
app = Flask(__name__)

@app.route("/")
def home():
    """
    home \n
    creates the homepage
    """
    return render_template("home.html")

@app.route("/compare", methods=["POST"])
def compare():
    """compare \n
    compares two mhbs"""

    data = request.get_json()
    file_name_1 = data.get('mhb1')
    file_name_2 = data.get('mhb2')

    file_names = [file_name_1, file_name_2]

    # allows to input either filenames (with or without .pdf at the end) or urls
    file_names = [i.split("/")[-1] if "/" in i else i for i in file_names]
    file_names = [i + ".pdf" if not ".pdf" in i else i for i in file_names]
    if any([False if i in os.listdir("pdfs") else True for i in file_names]):
        Exception("No valid pdf files")

    modules = [prt.Modules("pdfs/" + i) for i in file_names]

    no_infos = "k.A."

    extracted_modules = [i.toc_module_codes() for i in modules]
    # sort in order to save operations in the next step
    extracted_modules.sort(key=lambda x: len(x))
    overlapping_modules = list(set(extracted_modules[0]).intersection(*extracted_modules[1:]))

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
    print(information_overlaps)
    return jsonify({"data": information_overlaps})

if __name__ == "__main__":
    app.run(debug=True)