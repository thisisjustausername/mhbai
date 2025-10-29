from dotenv import load_dotenv, set_key
import os

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