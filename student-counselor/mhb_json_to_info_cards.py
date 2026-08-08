"""
Create info cards for RAG on module handbooks
"""

import json
import os
from pathlib import Path

from xml_processing.pipeline import get_files

base_path = Path(os.path.expanduser('~/mhbai/ai/compressed_mhbs'))
files = get_files(path_to_file=base_path, file_type='json')
files = [i for i in files if i.stem != 'metadata']

study_programs = []
lens = []

for file in files:
    with open(file, "r") as f:
        data = json.load(f)
    try:
        name = data['name']
    except TypeError:
        continue
    start_semester = data['start_semester']
    faculties = data['faculties']
    course_group = data['mhb_group']
    modules = []
    for group in data['module_groups']:
        for module in group['modules']:
            mdl = {
                "name": module['name'],
                "module_code": module['module_code'],
                "ects": module['ects'],
            }
            exams = [module.get('exam', {}), *module.get('exams', []), *[i.get('exams', []) for i in module.get('parts', [])]]
            exams = [(exam.get('name', None), exam.get('id', None)) for exam in exams if exam != {}]
            exams = set(exams)
            exams = [{"name": exam[0], "id": exam[1]} for exam in exams]
            mdl['exams'] = exams
            mdl['content'] = module['content']
            mdl['goals'] = module['goals']
            mdl['faculty_chair'] = a if len(a := module['faculty_chair']) == 1 else ', '.join(a)

            clean_module = {
                "name": mdl['name'],
                "module_code": mdl['module_code'],
                "ects": mdl['ects'],
                "exams": ', '.join(f'{i["name"]}: {i["id"]}' for i in mdl['exams']),
                "faculty_chair": ', '.join(mdl['faculty_chair']),
                "content": mdl['content'],
                "goals": mdl['goals'],
            }

            str_module = f"""Name: {clean_module['name']}
Modulcode: {clean_module['module_code']}
ECTS: {clean_module['ects']}
Prüfungen: {clean_module['exams']}
Lehrstühle: {clean_module['faculty_chair']}
Inhalt: {clean_module['content']}
Ziele: {clean_module['goals']}"""

            modules.append(str_module)

    output = f"""Studiengang: {name},
Startsemester: {start_semester},
Fakultäten: {', '.join(faculties)},
Studiengangsgruppe: {course_group},
Module:
    {',\n'.join('  --- NEUES MODUL ---\n' + '\n'.join('    ' + e for e in i.split('\n')) for index, i in enumerate(modules))}"""

    study_programs.append((str(file), output))

with open("student-counselor/info-cards-mhbs.json", "w") as f:
    json.dump(study_programs, f, indent=4, ensure_ascii=True)

print(study_programs[0])
