# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: save data from MHB to json
# Status: FINISHED

from pdf_reader.MHB_Overlaps import Overlaps
from pdf_reader.MHB import MHB
import json
import os

mhbs = os.listdir("pdfs")

length = len(mhbs)

i = mhbs[0]

def dictToTuple(d: dict[str, str | int | None]):
    return tuple([(k, v if type(v) != list else tuple(v)) for k, v in d.items()])

def tupleToDict(t: tuple):
    return {k: v for k, v in t}

mhb = MHB("pdfs/" + i)

all_mhbs= []
error_files = []
look_up_dict = {}


for index, i in enumerate(mhbs):
    print(f"{index+1} / {length}")
    try:
        mhb = MHB("pdfs/" + i)
    except (IndexError, AssertionError, ValueError):
        error_files.append(i)
        continue
    mhb_dict = {"title": mhb.title, "name": mhb.name, "modules": mhb.modules, "module_codes": mhb.module_codes}
    look_up_dict[i] = mhb_dict
    all_mhbs += mhb_dict["modules"]

tupled_data = [dictToTuple(i) for i in all_mhbs] # type: ignore

clean_modules = list(set(tupled_data))

mhbs = [tupleToDict(i) for i in clean_modules] # type: ignore

with open("uni_augsburg_module_data.json", "w") as file:
    json.dump(mhbs, file, indent=4)

with open("web_service/uni_augsburg_look_up.json", "w") as file:
    json.dump(look_up_dict, file, indent=4)

with open("uni_augsburg_error_files.json", "w") as file:
    json.dump(error_files, file, indent=4)