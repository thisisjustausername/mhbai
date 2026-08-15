'''
Check the uniqueness of the data and its quality before bulk inserting into the mongodb
'''

import json
import os
from collections import defaultdict
from pathlib import Path

from xml_processing.pipeline import get_files

base_path = Path(os.path.expanduser('~/mhbai/ai/compressed_mhbs'))
files = get_files(path_to_file=base_path, file_type='json')
files = [i for i in files if i.stem != 'metadata']


############
# 1. Check uniqueness of exams
############

grouped_exams = defaultdict(set)

for file in files:
    with open(file, 'r') as f:
        data = json.load(f)
    try:
        data['path']
    except TypeError:
        continue
    for group in data['module_groups']:
        for module in group['modules']:
            for exam in module['exams']:
                grouped_exams[exam['id']].add(tuple(v for k, v in exam.items() if k != 'description'))

print(f'Minimum exam id: {min(grouped_exams.keys())}')
print(f'Maximum exam id: {max(grouped_exams.keys())}')
print()

for i in grouped_exams:
    if len(grouped_exams[i]) > 1 and len({e[0] for e in grouped_exams[i]}) > 1:
        print(f'Exam id {i} has {len({e[0] for e in grouped_exams[i]})} unique name entries: \n{"\n".join(set("   " + e[0] for e in grouped_exams[i]))}')
