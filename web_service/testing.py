import time

import backend.pdf_reader_toc as prt
import timeit
import pdf_extracter as extr

"""times = 1000
execution_time = timeit.timeit(lambda: prt.toc_module_codes("backend/test_pdf.pdf"), number=times)
length = len(prt.toc_module_codes("backend/test_pdf.pdf"))
print(f"It approximately take-s {execution_time*1000/times:.4f} milliseconds to find {length} modules in the toc of a single mhb.\nThat's around {execution_time*1000/times/length:.4f}ms per module code."""

start = time.time_ns()
modules_1 = prt.toc_module_codes("backend/test_pdf.pdf")
modules_2 = prt.toc_module_codes("backend/geo_test.pdf")

print([i for i in modules_1 if i in modules_2])

print((time.time_ns() - start)/10e6)