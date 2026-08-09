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

from bson import ObjectId
from pymongo import MongoClient, ReturnDocument
from pymongo.collection import Collection
from tqdm import tqdm

from xml_processing.pipeline import get_files


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


base_path = Path(os.path.expanduser('~/mhbai/ai/compressed_mhbs'))
files = get_files(path_to_file=base_path, file_type='json')
files = [i for i in files if i.stem != 'metadata']

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

                # NOTE: do not change anything in exam after creating '_hash'-key
                exam['_hash'] = create_unique_hash(exam)
                exam_doc_id = insert_non_dupl(exams, exam)
                new_exams.append(exam_doc_id)
            mod['exams'] = new_exams if len(new_exams) > 0 else None

            # NOTE: do not change anything in mod after creating '_hash'-key
            mod['_hash'] = create_unique_hash(mod)
            mod_doc_id = insert_non_dupl(modules, mod)
            new_modules.append(mod_doc_id)
        group['modules'] = new_modules if len(new_modules) > 0 else None
    data['compressed_path'] = str(file)
    if len(data['module_groups']) == 0:
        data['module_groups'] = None
    insert_non_dupl(mhbs, data, 'path')
