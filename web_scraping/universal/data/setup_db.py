<<<<<<< Updated upstream
from dotenv import load_dotenv, set_key
import os
=======
# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: setup database connection parameters
# Status: VERSION 1.0

from dotenv import load_dotenv, set_key
>>>>>>> Stashed changes

"""
# Set path for .env file
env_path = os.getcwd().split("/mhbai")[0] + "/mhbai/.env"
"""

# Load environment variables from .env file
load_dotenv()
USERDB = 'gatterle'
HOST = 'localhost'
PORT = '5432'
DBNAME = 'mhbs'
PASSWORD = input("Enter database password: ")
set_key('.env', 'USERDB', USERDB)
set_key('.env', 'HOST', HOST)
set_key('.env', 'PORT', PORT)
set_key('.env', 'DBNAME', DBNAME)
set_key('.env', 'PASSWORD', PASSWORD)