# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# For usage please contact the developer.
#
# This file is Copyright-protected.

# Description: api starter
# Status: VERSION 1.0
# FileID: Ap-x-0001

"""
Starts and manages Flask API using waitress
"""

from waitress import serve

from api import api

def run_flask():
    """
    Docstring for run_flask
    """
    serve(api.app, host="127.0.0.1", port=5000)


if __name__ == "__main__":
    run_flask()