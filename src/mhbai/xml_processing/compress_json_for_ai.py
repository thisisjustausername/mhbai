"""
Compress the created json files by removing unnecessary ids, replacing id references with explicit objects, ...
Create SQL tables for objects in json files for graph like reference analysis
"""

import os


base_path = os.path.expanduser("~/mhbai/uni-a_mhbs_json/")
file_path = ("BachelorStudiengaenge/Bachelor\\ of\\ Arts\\ (Haupt\\ und\\ Nebenfach)/Erste\\ PO\\ des\\ Studiengangs\\ (ausgelaufen)\Sommersemester\\ 2016/Bachelor_of_Arts_AnglistikAmerikanistik_Hauptfach_BaPO_2008_ID22363_1_de_20160229_1229.json")

path = os.path.join(base_path, file_path)

with open(path, 'r') as f:
    data = f.read()

