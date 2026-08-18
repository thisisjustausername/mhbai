# %% Import
import pandas as pd
from pymongo import MongoClient

# %% Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['unia']
mhbs = db['mhbs']
modules = db['modules']
exams = db['exams']

# %% Query the database
res = mhbs.count_documents({})
print(res)
# %% Look at documents
docs = list(mhbs.find())
df = pd.DataFrame(docs)
print(df.head(3))


# %% Clear the database and verify
# mhbs.delete_many({})
# modules.delete_many({})
# exams.delete_many({})
#
# print(f'MHBS count after deletion: {mhbs.count_documents({})}')
# print(f'Modules count after deletion: {modules.count_documents({})}')
# print(f'Exams count after deletion: {exams.count_documents({})}')
#
