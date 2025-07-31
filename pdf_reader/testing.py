from pdf_reader.MHB import MHB
import pdf_reader.pdf_reader_toc as prt

name = "pdfs/Modulhandbuch_Bachelor_of_Music_PO_2023_ID48735_5_de_20250414_1754.pdf"
mhb = MHB(name)
print(mhb.name, mhb.title)
"""mhb = prt.Modules(name)
modules = mhb.toc_module_codes()
module_code = "MUS-5113"
for i in modules:
    info = mhb.data_to_module(i)
    print(info["module_code"], info["title"])"""