import pdf_extracter as extr
import re
from itertools import groupby
import json

def toc_module_codes(pdf_path):
    pdf = extr.Pdf(pdf_path=pdf_path)
    data = pdf.extract_objects()
    data = [i["object_data"] for i in data if i["information"] == "success"]

    # this identifies every page of the toc
    # toc_identifier = "BT\n/F1 12 Tf\n1 0 0 -1 0 10.26599979 Tm [(Inhaltsverzeichnis)] TJ\nET"
    toc_pages = [i for i in data if "Inhaltsverzeichnis" in i]
    text_orientation = r'1 0 0 -1'
    position = r'\d+(?:\.\d+)? \d+(?:\.\d+)?'
    # Tm sets the text positioning
    # TJ shows the text individually

    module_code = text_orientation + r' ' + position + r' Tm\s?\[\([^\\n\r]*?\)'

    matches_list = []
    for i in toc_pages:
        page_matches = re.findall(module_code, i)
        matches_list.append(page_matches)
    # matches is made out of the match the height coordinate and the width coordinate
    # WATCH OUT instantly casting to float can cause exceptions really quickly. Keep this simply for debugging
    matches = [[e, float(re.search(r'\d+(?:\.\d+) Tm', e).group(0)[:-3]), float(re.search(r'1 0 0 -1 \d+(?:\.\d+)?', e).group(0)[9:])] for i in matches_list for e in i]
    # remove dots
    # removing dots in advance saves time but makes result little less accurate since it cant be verified that some unexpected data was accidentally selected
    matches = [i for i in matches if " Tm [(.)" not in i[0]]
    # split matches in lines
    # not sorting so that just lines that are together are packed together in order to not ignore page breaks
    # WATCH OUT with the current code also when a line goes over two pages it is being broken up and ignored
    #matches.sort(key=lambda x: x[1])
    lines = [list(group) for key, group in groupby(matches, key=lambda x:x[1])]
    # TODO in the current code page breaks are ignored. this creates the error of mixing module codes, that are on the same height but on different pages. Fix it by either not ignoring line breaks or making it a different height, when between it is a different height, e.g. by not sorting list before grouping it
    # get page number and module code
    modules = []
    # TODO if the page number is in the next line, still take it
    # for now simply ignore page number
    for line in lines: # go through every line
        # is_module = False # if module code is found set to true TODO uncomment if using page numbers
        # module = [] TODO uncomment if using page numbers
        for part in line: # for every part in the line, check whether it is a module code
            # TODO uncomment if using page numbers
            # if not is_module:  # if it is not the first module code, then ignore it
            code = re.search(r' Tm \[\([A-ZÄÖÜ]{2,}-\d{3,}', part[0])
            if code is not None: # if module code is found, execute this
                # TODO uncomment if using page numbers
                # is_module = True # set module code to True
                modules.append(code.group(0)[6:])
                # module.append(code.group(0)[6:-2]) # append the code to the module list TODO uncomment if using page numbers
                break # TODO comment this if using page numbers
            # ignore page number
            # TODO when uncommenting do this: if the page number is in the next line, still take it
            r"""else: # if a module code was already found, then search for page numbers
                page_number = re.search(r' Tm \[\(\d+\)\]', part[0]) # search for page number
                if page_number is not None: # if page number was found, execute this
                    module.append(page_number.group(0)[6:-2]) # add page number to module list
        if len(module) > 2: # if the module contains more than one page number, just keep the last one
            module = [module[0], module[-1]]"""

    # remove duplicates
    modules = list(set(modules))
    return modules