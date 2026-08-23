'''
Fill the unia studis mhb database with the studis compressed json documents
Additionally clean the data beforehand
'''
import hashlib
import json
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Literal, overload

from bson import ObjectId
from langchain_ollama import OllamaEmbeddings
from pymongo import MongoClient, ReturnDocument, UpdateOne
from pymongo.collection import Collection
from tqdm import tqdm

from mongo_db.init_vector_search import collections, embedded_keys
from xml_processing.pipeline import get_files

embeddings = OllamaEmbeddings(model="qwen3-embedding")


def retype_objectid_to_str(data: dict | list):
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, ObjectId):
                data[k] = str(v)
            elif isinstance(v, (dict, list)):
                data[k] = retype_objectid_to_str(v)
    elif isinstance(data, list):
        data = [retype_objectid_to_str(item) if isinstance(item, (list, dict)) else item if not isinstance(item, ObjectId) else str(item) for item in data]
    return data


# NOTE: DO NOT HASH THE EMBEDDING VECTOR FIELDS!!!
def create_unique_hash(doc: dict) -> str:
    '''
    Create an almost unique hash for a document based on its content. This is used to identify duplicates.
    NOTE: make sure all sortable fields like lists are sorted

    Args:
        doc (dict): The document to create a hash for.
    Returns:
        str: The sha-256 hashed content of the document.
    '''
    string = json.dumps(retype_objectid_to_str(deepcopy(doc)), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(string.encode('utf-8')).hexdigest()


def infocard(data: dict, collection: Literal['mhbs', 'modules', 'exams'] | None) -> str:
    '''
    Create an infocard from a dictionary of key-value pairs to embed infocard and perform vector search on it.

    Args:
        data (dict): A dictionary containing key-value pairs.
        collection (Literal['mhbs', 'modules', 'exams'] | None): The collection name to which the infocard belongs, if None no keys will be sorted out by collection.
    Returns:
        str: A formatted string representing the infocard.
    '''
    # order for the keys in the infocard (combines mhbs, modules and exams but the keys are almost distinct or the position matches)
    order = ['name', 'description', 'path', 'faculties', 'faculty_chair', 'prerequisites', 'lecturer', 'type', 'frequency', 'preparation', 'duration', 'success_requirements', 'workloads', 'goals', 'content']

    # replace shallow (only!) None values with Unknown
    data = {k: (v if v is not None else 'Unknown') for k, v in data.items()}

    # unnest nested values for mhbs collection
    if 'faculties' in data:
        data['faculties'] = ', '.join(data['faculties'])
    if 'module_groups' in data and data['module_groups'] != 'Unknown':
        data['module_groups'] = [f'    name: {mg["name"]}\n    needed / allowed ects: {mg["min_ects"]} - {mg["max_ects"]}\n    modules: {", ".join(mg["modules"])}' for mg in data['module_groups']]
    # clean path (for security reasons too)
    if 'path' in data:
        data['path'] = data['path'].split('uni-a_mhbs_json/', 1)[1]

    # unnest nested values for modules collection
    if 'languages' in data and data['languages'] != 'Unknown':
        data['languages'] = ', '.join(data['languages'])
    if 'workloads' in data and data['workloads'] != 'Unknown':
        data['workloads'] = ';\n'.join([f'    name: {wl["name"]}\n    in presence: {wl["in_presence"]}\n    time expenditure in hours: {wl["time_expenditure"]}' for wl in data['workloads']])
    if 'recommended_semester_span' in data and data['recommended_semester_span'] != 'Unknown':
        data['recommended_semester_span'] = 'start: ' + (data['recommended_semester_span']['start_semester'] or 'Unknown') + ', end: ' + (data['recommended_semester_span']['end_semester'] or 'Unlimited')
    if 'available_semesters' in data:
        data['available_semesters'] = 'start: ' + (data['available_semesters']['start_semester'] or 'Unknown') + ', end: ' + (data['available_semesters']['end_semester'] or 'Unlimited') + ', frequency: ' + (data['available_semesters']['frequency'] or 'Unknown')

    infocard = ';\n'.join(f"{k}: {data[k]}" for k in order if k in data and (collection is None or k in embedded_keys[collection]))  # order the keys according to the order list and filter out any other keys
    return infocard.strip()


# NOTE: DO NOT HASH THE EMBEDDING VECTOR FIELDS!!!
@overload
def create_embedding_vector(data: str | list | dict, return_embeddings: Literal[True] = True) -> list[float]: ...

@overload
def create_embedding_vector(data: str | list | dict, return_embeddings: Literal[False]) -> str: ...

def create_embedding_vector(data: str | list | dict | None, return_embeddings: bool = True) -> list[float] | str | None:
    '''
    Create an embedding vector for data or simply an infocard for the data.

    Args:
        data (str | list | dict | None): The data to create an embedding vector for.
    Returns:
        list[float] | None: The embedding vector for the data.
    '''
    if data is None:
        return None
    if isinstance(data, list): # e.g. for faculties
        if len(data) > 0 and isinstance(data[0], dict):
            data = [infocard(d, collection=None) for d in data]
        data = ', '.join(data)
    elif isinstance(data, dict):
        data = infocard(data, collection=None)
    if return_embeddings is False:
        return data
    return embeddings.embed_query(data)


def insert_non_dupl(collection: Collection, doc: dict, check_attr: str = '_hash') -> ObjectId:
    '''
    Insert a document into a collection if it does not already exist based on its unique hash.

    Args:
        collection (Collection): The MongoDB collection to insert the document into.
        doc (dict): The document to insert.
        check_attr (str): The attribute to check for duplicates (e.g., '_hash').
    Returns:
        ObjectId: The ID of the inserted or existing document.
    '''
    return collection.find_one_and_update(
        {'_hash': doc[check_attr]},
        {'$setOnInsert': doc},
        upsert=True,
        projection={"_id": 1},
        return_document=ReturnDocument.AFTER
    )['_id'] # type: ignore


client = MongoClient('mongodb://localhost:27017/')
db = client['unia']
mhbs = db['mhbs']
modules = db['modules']
exams = db['exams']


def batch_embedding_to_mongo(collection: Literal['mhbs', 'modules', 'exams'], batch_size: int = 64):
    '''
    Batch embedding of documents in a collection and storing the embeddings in the same collection.

    Args:
        collection (Literal['mhbs', 'modules', 'exams']): The collection to embed documents from.
        batch_size (int): The number of documents to process in each batch.
    '''
    keys = embedded_keys[collection]
    docs = db[collection].find({key: {'$ne': None} for key in keys}, projection={key: 1 for key in keys})

    pending = [
        (doc['_id'], key, val) for doc in docs for key, val in doc.items() if key != '_id'
    ]

    for i in tqdm(range(0, len(pending), batch_size)):
        batch = pending[i:i + batch_size]
        texts = [create_embedding_vector(val, return_embeddings=False) for _, _, val in batch]

        vecs = embeddings.embed_documents(texts)

        ops = [
            UpdateOne({'_id': doc_id}, {'$set': {f'embedding_{key}': vec}}) for (doc_id, key, _), vec in zip(batch, vecs)
        ]
        db[collection].bulk_write(ops)


base_path = Path(os.path.expanduser('~/mhbai/ai/compressed_mhbs'))
files = get_files(path_to_file=base_path, file_type='json')
files = [i for i in files if i.stem != 'metadata']

# NOTE: DO NOT HASH THE EMBEDDING VECTOR FIELDS!!!
for file in tqdm(files):
    with open(file, 'r') as f:
        data = json.load(f)
    try:
        data['path']
    except TypeError:
        continue
    for group in data['module_groups']:
        new_modules = []
        mdls = group.pop('modules', None)
        for module in mdls:
            mod = deepcopy(module)
            mod.pop('parts', None)
            mod.pop('description', None)
            mod.pop('module_part_combinations', None)
            mod.pop('keywords', None)
            mod.pop('usability', None)
            mod.pop('prerequisite_language', None)
            mod['languages'] = None if mod['languages'] is None or mod['languages'] == [] else sorted(mod['languages'])
            mod['faculty_chair'] = None if mod['faculty_chair'] is None or mod['faculty_chair'] == [] else mod['faculty_chair'][0]
            if isinstance(mod['ects'], str):
                mod['ects'] = int(float(mod['ects'].replace(',', '.')))
            if len(mod['workloads']) == 0:
                mod['workloads'] = None
            if mod['mandatory'] in [0, 1]:
                mod['mandatory'] = bool(mod['mandatory'])
            if isinstance(mod['success_requirements'], int) and mod['success_requirements'] == mod['ects']:
                mod['success_requirements'] = 'Erreichen aller ECTS-Punkte'
            if isinstance(mod['prerequisites'], dict):
                mod['prerequisites'] = mod['prerequisites'].get('html', {}).get('body', None)
            if not re.match(r'^[A-ZÄÖÜ]{3}-\d{4}[a-z]?$', mod['module_code']) and re.match(r'^[A-ZÄÖÜ]{3}-\d{4}[a-z]?$', mod['module_code'].upper()):
                mod['module_code'] = mod['module_code'].upper()

            if (a := mod.get('recommended_semester_span', {})) is not None and a.get('end_semester', None) == 0:
                mod['recommended_semester_span']['end_semester'] = 99
            if (a := mod.get('recommended_semester_span', {})) is not None and a.get('start_semester', None) == 0:
                mod['recommended_semester_span']['start_semester'] = 99

            exms = mod.pop('exams', None)
            new_exams = []
            for exam in exms:
                exam.pop('languages', None)
                exam['frequency'] = exam.pop('exam_frequency', None)
                if exam['portion_of_grade'] is not None and isinstance(exam['portion_of_grade'], str):
                    exam['portion_of_grade'] = int(float(exam['portion_of_grade'].replace(',', '.')))

                if isinstance(exam['description'], dict):
                    exam['description'] = exam['description'].get('html', {}).get('body', None)

                # NOTE: do not change anything in exam after creating '_hash'-key except for adding embedding vectors
                exam['_hash'] = create_unique_hash(exam)

                # NOTE: DO NOT HASH THE EMBEDDING VECTOR FIELDS!!!
                # for key in embedded_keys['exams']:
                #     exam[f'embedding_{key}'] = create_embedding_vector(exam[key])

                exam_doc_id = insert_non_dupl(exams, exam)
                new_exams.append(exam_doc_id)
            mod['exams'] = new_exams if len(new_exams) > 0 else None

            # NOTE: do not change anything in mod after creating '_hash'-key except for adding embedding vectors
            mod['_hash'] = create_unique_hash(mod)

            # NOTE: DO NOT HASH THE EMBEDDING VECTOR FIELDS!!!
            # for key in embedded_keys['modules']:
            #     mod[f'embedding_{key}'] = create_embedding_vector(mod[key])

            mod_doc_id = insert_non_dupl(modules, mod)
            new_modules.append(mod_doc_id)
        group['modules'] = new_modules if len(new_modules) > 0 else None
    data['compressed_path'] = str(file)
    if len(data['module_groups']) == 0:
        data['module_groups'] = None

    # NOTE: DO NOT HASH THE EMBEDDING VECTOR FIELDS!!!
    # for key in embedded_keys['mhbs']:
    #     data[f'embedding_{key}'] = create_embedding_vector(data[key])
    insert_non_dupl(mhbs, data, 'path')

for collection in collections:
    batch_embedding_to_mongo(collection, batch_size=64)
