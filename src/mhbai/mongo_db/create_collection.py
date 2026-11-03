'''
Create mongodb for compressed STUDIS mhb json files and extracted json files.
'''

import json

from pymongo import ASCENDING, IndexModel, MongoClient

with open('src/mongo_db/collection_schemata.json', 'r') as f:
    schemata = json.load(f)

client = MongoClient('mongodb://localhost:27017/')

# create / access db
db = client['unia']

# create / access collections

db.create_collection(
    'mhbs',
    validator=schemata['mhbs']
)
mhbs = db['mhbs']
mhbs.create_indexes([
    IndexModel([('compressed_path', ASCENDING)], unique=True),
    IndexModel([('path', ASCENDING)], unique=True)
])


# NOTE: ignore parts, description, module_part_combinations, keywords, usability as they are always either None or []
# NOTE: ignore prerequisite_language as it mostly contains the same information as prerequisites
# NOTE: simply pick first item from faculty_chair as it is always only one item
db.create_collection(
    'modules',
    validator=schemata['modules']
)

modules = db['modules']
modules.create_index('_hash', unique=True)


# NOTE: ignore languages as it is always None
db.create_collection(
    'exams',
    validator=schemata['exams']
)

exams = db['exams']
exams.create_index('_hash', unique=True)
