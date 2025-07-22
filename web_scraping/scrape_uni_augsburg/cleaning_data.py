# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

import json

# load the data to all modules
with open("pdf_data.json", "r") as file:
    data = json.load(file)

# flatten the list of module information (remove the assignment from modules to their courses of study)
module_list = [e for i in data for e in i["modules"]]

# cast dicts to tuples in order to compare them and remove duplicates
module_tuples = [tuple([e for e in i.items()]) for i in module_list]

# remove duplicates
clean_data = list(set(module_tuples))

print(f"{len(module_tuples)} -> {len(clean_data)}")

clean_dicts = [dict(i) for i in clean_data] # convert tuples back to dicts

# save data
with open("clean_module_infos.json", "w") as file:
    json.dump(clean_dicts, file)

# remove all modules, where either, tile, content or goals is missing
complete_information = [i for i in clean_data if all([True if e != "" else False for e in i.values()])]
print(len(complete_information))

# save data
with open("complete_information.json", "w") as file:
    json.dump(complete_information, file)