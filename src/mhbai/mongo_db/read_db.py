# %% Import
import os

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()  # Load environment variables from .env file

# %% Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')# , authSource='unia', username='unia-search-ai', password=os.getenv('MONGO_DB_UNIA_SEARCH_AI_PASSWORD'))
db = client['unia']
mhbs = db['mhbs']
modules = db['modules']
exams = db['exams']

# %% Query the database
res = mhbs.count_documents({})
print(res)
# %% Inspect mhb documents
docs = list(mhbs.find())
df = pd.DataFrame(docs).keys()
print(df)
print(mhbs.find_one())
'''
description
faculties
mhb_group
module_groups
name
'''

# %% Inspect module documents
docs = list(modules.find())
df = pd.DataFrame(docs).keys()
print(df)
'''
content
goals
exam_outline
faculty_chair
lecturer
name
prerequisites
success_requirements
workloads
'''

# %%
docs = list(mhbs.find({}, {'description': 1}))
docs = set(i['description'] for i in docs if i['description'] is not None)
for i in docs:
    if not i.startswith('Studienbeginn'):
        print(i)


# %%
docs = {e for i in list(modules.find({}, {'languages': 1})) if i['languages'] is not None for e in i['languages']}
print(docs)

# %% Inspect exam documents
docs = list(exams.find())
df = pd.DataFrame(docs).keys()
print(df)
'''
description
duration
frequency
name
preparation
type
'''

# %% Clear the database and verify
'''for index in mhbs.list_search_indexes():
    name = index["name"]
    print(f"Dropping search index: {name}")
    mhbs.drop_search_index(name)
for index in modules.list_search_indexes():
    name = index["name"]
    print(f"Dropping search index: {name}")
    modules.drop_search_index(name)
for index in exams.list_search_indexes():
    name = index["name"]
    print(f"Dropping search index: {name}")
    exams.drop_search_index(name)
mhbs.drop()
modules.drop()
exams.drop()'''
'''mhbs.delete_many({})
modules.delete_many({})
exams.delete_many({})

print(f'MHBS count after deletion: {mhbs.count_documents({})}')
print(f'Modules count after deletion: {modules.count_documents({})}')
print(f'Exams count after deletion: {exams.count_documents({})}')'''
