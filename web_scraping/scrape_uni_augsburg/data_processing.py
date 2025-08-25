# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: extract data from pdfs and save them in json, clean data afterwards using cleaning_data.py

# IMPORTANT NOTE: run this code on remote host

from pdf_reader import pdf_reader_toc as prt
import os
import json

# retrieve the names of all pdfs
all_pdfs = os.listdir("pdfs")

# in these lists save all mhbs and modules, where errors occured
error_pdfs = []
error_modules = []

successful_data = [] # save all the data, that was successfully extracted

# iterate through all mhbs
for index, i in enumerate(all_pdfs):
    print(index) # print index to show the process

    # try to extract the module codes from toc
    try:
        Modules = prt.Modules("pdfs/" + i)
        module_codes = Modules.toc_module_codes()
    except:
        error_pdfs.append(i)
        print(f"TOC error: {i}")
        continue

    # not checking, whether information to the current module code was already extracted, in case that two mhbs contain the same module with different information
    # try to extract the infos from each module
    mhb = []
    for module in module_codes:
        try:
            information = Modules.data_to_module(module)
            mhb.append(information)
        except:
            error_modules.append(module)
            print(f"Module error: {module}")
            continue

    # add the data as a dict
    data = {"mhb": i, "modules": mhb}
    successful_data.append(data)

# save data
with open("pdf_data.json", "w") as file:
    json.dump(successful_data, file)