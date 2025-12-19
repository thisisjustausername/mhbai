from database import database as db
from ai.overall_ai.data_extraction import extract_module_info as emi
from pdf_reader import pdf_reader_toc as prt

import json

pdf_path = "pdfs/40.pdf"

modules: prt.Modules = prt.Modules(pdf_path=pdf_path)
module_pages = modules.raw_module_texts()
for i in module_pages:
    print(i["module_code"])
    print(i["content"])
    print("------------------------------------------")
# print(json.dumps(module_pages, indent=4))
