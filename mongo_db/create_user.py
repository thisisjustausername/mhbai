import getpass
import os

from dotenv import load_dotenv, set_key
from pymongo import MongoClient

env_path = os.path.join('./', '.env')
load_dotenv(dotenv_path=env_path)

# only works when no admin account exists yet
client = MongoClient("mongodb://localhost:27017/?replicaSet=rs0")
admin_db = client["admin"]

password = getpass.getpass("Enter password for admin user: ")

admin_db.command(
    "createUser",
    "admin",
    pwd=password,
    roles=["root"]
)

print("User created successfully.")
set_key(env_path, 'MONGO_DB_ADMIN_PASSWORD', password)
client.close()

# unnecessary, but used as blueprint for login
password = getpass.getpass("Admin password: ")
client = MongoClient(
    'mongodb://localhost:27017/?replicaSet=rs0',
    username='admin',
    password=password,
    authSource='admin'
)


db = client['unia']

password = getpass.getpass("Enter password for unia-search-ai user: ")

db.command(
    "createRole",
    "Unia-Search",
    privileges=[
        {
            'resource': {'db': 'unia', 'collection': ''},
            'actions': ['find']
        }
    ],
    roles=[]
)

db.command(
    "createUser",
    "unia-search-ai",
    pwd=password,
    roles=["Unia-Search"]
)

print("User created successfully.")
set_key(env_path, 'MONGO_DB_unia-search-ai_PASSWORD', password)
client.close()
