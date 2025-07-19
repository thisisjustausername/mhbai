import traceback

import web_service.backend.pdf_reader_toc as prt
import os
import json

# run this code on remote host
all_pdfs = os.listdir("pdfs")

error_pdfs = []
error_modules = []

successful_data = []
for index, i in enumerate(all_pdfs):
    print(index)
    try:
        Modules = prt.Modules("pdfs/" + i)
        module_codes = Modules.toc_module_codes()
    except:
        error_pdfs.append(i)
        print(f"TOC error: {i}")
        print(traceback.format_exc())
        breakpoint()
        continue
    mhb = []
    for module in module_codes:
        try:
            information = Modules.data_to_module(module)
            mhb.append(information)
        except:
            error_modules.append(module)
            print(f"Module error: {module}")
            continue
    data = {"mhb": i, "modules": mhb}
    successful_data.append(data)


with open("pdf_data.json", "w") as file:
    json.dump(successful_data, file)