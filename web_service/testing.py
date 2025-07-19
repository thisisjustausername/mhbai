import json
import time

import backend.pdf_reader_toc as prt
import timeit
import pdf_extractor as extr

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

