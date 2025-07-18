from flask import Flask, session, g, flash, render_template, request, redirect, url_for, make_response, jsonify
import WebScraping.scrape_uni_augsburg.download_files as df
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

    file_url_1 = request.form.get("file_url_1")
    file_url_2 = request.form.get("file_url_2")

    if not (df.check_url(file_url_1) and df.check_url(file_url_2)):
        return jsonify({"error": '''The url seems to be invalid. Make sure it starts with "https://mhb.uni-augsburg.de/", ends with ".pdf" and isn't longer than 500 characters'''})

    