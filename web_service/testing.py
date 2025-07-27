# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

from pdf_reader import pdf_reader_toc as prt
from pdf_reader.MHB_Overlaps import Overlaps
from pdf_reader.MHB import MHB
import json
"""times = 1000
execution_time = timeit.timeit(lambda: prt.toc_module_codes("backend/test_pdf.pdf"), number=times)
length = len(prt.toc_module_codes("backend/test_pdf.pdf"))
print(f"It approximately take-s {execution_time*1000/times:.4f} milliseconds to find {length} modules in the toc of a single mhb.\nThat's around {execution_time*1000/times/length:.4f}ms per module code."""

"""start = time.time_ns()
module_1 = prt.Modules("backend/test_pdf.pdf")
module_2 = prt.Modules("backend/geo_test.pdf")
codes_1 = module_1.toc_module_codes()
codes_2 = module_2.toc_module_codes()
overlapping = [i for i in codes_1 if i in codes_2]
ects_overlapping = sum([module_1.data_to_module(i)["ects"] for i in overlapping])
duration = (time.time_ns() - start)/10e6
print(f"It takes {duration:.2f}ms to compare two pdfs.")"""
"""start = time.time()
modules = prt.Modules("backend/test_pdf.pdf")
for i in range(1000):
    modules.toc_module_codes()
end = time.time()
print((end - start)/ 1000)"""

"""start = time.time_ns()
module_1 = prt.Modules("backend/test_pdf.pdf")
codes_1 = module_1.toc_module_codes()


module_2 = prt.Modules("backend/geo_test.pdf")
codes_2 = module_2.toc_module_codes()
start = time.time()
for i in module_2.module_codes:
    module_2.data_to_module(i)

for i in module_1.module_codes:
    module_1.data_to_module(i)
end = time.time()
print((end - start) / (len(module_1.module_codes + module_2.module_codes)))
end = time.time_ns()
print((end - start)*10e-10)"""

"""module_2 = prt.Modules("pdfs/Bachelorstudiengang_Mathematik_ID16200_17_de_20231122_1210.pdf")
codes_2 = module_2.toc_module_codes()
for i in codes_2:
    if i == "MTH-1302":
        print(module_2.data_to_module(i))"""
#mhb = MHB("pdfs/Bachelorstudiengang_Data_Science_ID40699_5_de_20241007_0959.pdf")
# mhb2 = MHB("pdfs/Bachelorstudiengang_Mathematik_ID16200_17_de_20231122_1210.pdf")
#overlaps = Overlaps([mhb, mhb2])

with open("web_scraping/scrape_uni_augsburg/links_information.json", "r") as file:
    links_data =  json.load(file)

def get_file_name(url: str) -> str:


    if url not in links_data.keys():
        return url.split("/")[-1]
    return links_data[url]
file_name = get_file_name("https://mhb.uni-augsburg.de/BachelorStudiengaenge/Bachelor+of+Arts+%28Hauptfach%29/Anwendungsorientierte+Interkulturelle+Sprachwissenschaft+%28Hauptfach%29/POVersion+2023/Wintersemester%202024_25/Bachelorstudiengang_Anwendungsorientierte_Interkulturelle_Sprachwissenschaft_ANIS_PO_2023.pdf")

mhb = MHB("pdfs/" + file_name)
#mhb.export("csv", "test")
mhb.export("html", "test")

"""with open("web_scraping/scrape_uni_augsburg/links_information.json", "r") as file:
    links_data =  json.load(file)

def get_file_name(url: str) -> str:


    if url not in links_data.keys():
        return url.split("/")[-1]
    return links_data[url]

url = "https://mhb.uni-augsburg.de/BachelorStudiengaenge/Bachelor+of+Science/Global+Business+Management+%28Hauptfach%29/POVersion+2015/Sommersemester%202025/Bachelorstudiengang_Global_Business_Management_PO_2015.pdf"

print(get_file_name(url))"""
