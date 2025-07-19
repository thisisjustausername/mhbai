from flask import Flask, session, g, flash, render_template, request, redirect, url_for, make_response, jsonify
#import web_scraping.scrape_uni_augsburg.download_files as df
import backend.pdf_reader_toc as prt
import os
app = Flask(__name__)

@app.route("/")
def home():
    """
    home \n
    creates the homepage
    """
    return render_template("/")

@app.route("/compare", methods=["POST"])
def compare():
    """compare \n
    compares two mhbs"""

    file_name_1 = request.form.get("file_url_1")
    file_name_2 = request.form.get("file_url_2")

    file_names = [file_name_1, file_name_2]

    # allows to input either filenames or urls
    file_names = [i.split("/")[-1] if "/" in i else i for i in file_names]

    if not (any([False if i in os.listdir("pdfs") else True for i in file_names])):
        return jsonify({"error": "File not found"})

    modules = [prt.Modules(i) for i in file_names]

    extracted_modules = [i.toc_module_codes() for i in modules]
    # sort in order to save operations in the next step
    extracted_modules.sort(key=lambda x: len(x))
    overlapping_modules = list(set(extracted_modules[0]).intersection(*extracted_modules[1:]))

    information_overlaps = [modules[0].data_to_module(i) for i in overlapping_modules]

    return information_overlaps

    #if not (df.check_url(file_url_1) and df.check_url(file_url_2)):
    #    return jsonify({"error": '''The url seems to be invalid. Make sure it starts with "https://mhb.uni-augsburg.de/", ends with ".pdf" and isn't longer than 500 characters'''})

    