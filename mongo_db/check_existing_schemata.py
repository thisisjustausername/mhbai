'''
Check, whether some of the fields existing in the compressed mhbs are always empty and therefore presumed unimportant
'''

import os
import json
from pathlib import Path
from xml_processing.pipeline import get_files

base_path = Path(os.path.expanduser('~/mhbai/ai/compressed_mhbs'))
files = get_files(path_to_file=base_path, file_type='json')
files = [i for i in files if i.stem != 'metadata']

def check_param(param: str, val = None):
    for file in files:
        with open(file, "r") as f:
            data = json.load(f)
        try:
            name = data['name']
        except TypeError:
            continue
        for group in data['module_groups']:
            for module in group['modules']:
                if module['recommended_semester_span']['end_semester'] < module['recommended_semester_span']['start_semester']:
                    print(module)



if __name__ == '__main__':
    for i in ['prerequisites']:
        print(i)
        check_param(i, [None, []])
        print()
