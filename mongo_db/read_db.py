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
mhbs.delete_many({})
modules.delete_many({})
exams.delete_many({})

print(f'MHBS count after deletion: {mhbs.count_documents({})}')
print(f'Modules count after deletion: {modules.count_documents({})}')
print(f'Exams count after deletion: {exams.count_documents({})}')
