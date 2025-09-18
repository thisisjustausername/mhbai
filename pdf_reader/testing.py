# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: used for testing pdf_reader_toc.py

from pdf_reader.MHB import MHB
import pdf_reader.pdf_reader_toc as prt
import json

name = "pdfs/Modulhandbuch_Bachelor_of_Music_PO_2023_ID48735_5_de_20250414_1754.pdf"
name = "pdfs/BA_Frankoromanistik_im_Austausch_Frankocom_PO_2014_ID22838_2_de_20181008_1434.pdf"
modules_data = prt.Modules(pdf_path=name) # temporary variable used to retrieve all necessary data
modules = modules_data.toc_module_codes()
for i in modules:
    result = modules_data.data_to_module(i)
    if all(i["exam"] is None for i in result["module_parts"]):
        print(result["module_code"])
        print("     " + json.dumps(result["module_parts"]))

# print(mhb.name, mhb.title)
# mhb.export("md", file_path=mhb.name, borders=False)
"""mhb = prt.Modules(name)
modules = mhb.toc_module_codes()
module_code = "MUS-5113"
for i in modules:
    info = mhb.data_to_module(i)
    print(info["module_code"], info["title"])"""