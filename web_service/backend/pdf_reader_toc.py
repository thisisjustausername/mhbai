import pdf_extracter as extr
import re
from itertools import groupby
from typing import Optional

# TODO cleanly comment this code

class Modules:
    def __init__(self, pdf_path: str):
        """
        __init__ \n
        :param pdf_path: path to pdf file
        """
        self.path: str = pdf_path
        self.pdf: extr.Pdf = extr.Pdf(pdf_path=self.path)
        self.content: list = self.pdf.extract_objects()
        self.stream_data: list = [i["data"] for i in self.content if i["information"] == "success"]
        self.module_codes: Optional[list] = None


    def toc_module_codes(self):
        # this identifies every page of the toc
        # toc_identifier = "BT\n/F1 12 Tf\n1 0 0 -1 0 10.26599979 Tm [(Inhaltsverzeichnis)] TJ\nET"
        toc_pages = [i for i in self.stream_data if "Inhaltsverzeichnis" in i]
        text_orientation = r'1 0 0 -1'
        position = r'\d+(?:\.\d+)? \d+(?:\.\d+)?'
        # Tm sets the text positioning
        # TJ shows the text individually

        module_code = text_orientation + r' ' + position + r' Tm\s?\[\([^\n\r]*?\)'

        matches_list = []
        for i in toc_pages:
            page_matches = re.findall(module_code, i)
            matches_list.append(page_matches)
        # matches is made out of the match the height coordinate and the width coordinate
        # WATCH OUT instantly casting to float can cause exceptions really quickly. Keep this simply for debugging
        matches = [[e, float(re.search(r'\d+(?:\.\d+)? Tm', e).group(0)[:-3]), float(re.search(r'1 0 0 -1 \d+(?:\.\d+)?', e).group(0)[9:])] for i in matches_list for e in i]
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

        # set class vars and return modules
        self.module_codes = modules
        return modules

    def data_to_module(self, module_code: str) -> Optional[dict]:
        """
        data_to_module \n
        :param module_code: module code of the module, that should be searched
        :type module_code: str
        :return: information to the module
        :rtype: Optional[dict
        """
        if self.module_codes is None:
            self.toc_module_codes()
        if module_code not in self.module_codes:
            return None
        matching_pages = [page for page in self.stream_data if re.search(r'Modul ' + module_code, page) is not None]

        # /F3 10 sets font and size
        titles = re.finditer(r'Tm \[\(Modul ' + module_code, matching_pages[0])
        title_start = [i for i in titles if len(matching_pages[0][i.start()-100: i.start()].split("\n")) > 1 and "/F3 10" in matching_pages[0][i.start()-100: i.start()].split("\n")[-2]][0].end()
        title_search = matching_pages[0][title_start:title_start+500]
        title_raw = re.search(r': [^\]]+\)\] TJ', title_search)
        if title_raw is None:
            title = None
        else:
            title = title_raw.group(0)[2:].split(")]")[-2]
        start_info = title_raw.end()

        ects = int(re.search(r' Tm \[\(\d+ ECTS/LP\)\] TJ', matching_pages[0][start_info:]).group(0).split("Tm [(", 1)[1].split("ECTS", 1)[0])

        def search_text_blocks(heading: str) -> str:
            """
            inside function search_text_blocks \n
            This function extracts text blocks for a specific heading in a module (e.g. Inhalt in a module) \n
            This only works when the box doesn't contain any subcells from the table
            :param heading: string to search for e.g. Inhalte:
            :type heading: str
            :return: the text block
            """
            information = [page[start_info:] for page in matching_pages]
            details_list = []
            for page in information:
                start = re.search(r' Tm \[\(' + heading + r'\)\] TJ', page)
                if start is None:
                    continue
                start = start.start()
                end = re.search(r'\nET\nQ', page[start:]).start()
                details_list.append(page[start:start + end])

            texts_raw = []
            for block in details_list:
                for element in block.split('\n'):
                    if not re.match(r'1 0 0 -1 ', element):
                        continue
                    text_raw = element[re.search(r' Tm \[\(', element).end():]
                    text_full = text_raw[:re.search(r'\)\] TJ', text_raw).start()]
                    raw_element = {"width": re.search(r'1 0 0 -1 \d+(?:\.\d+)?', element).group(0)[9:],
                                   "height": re.search(r' \d+(?:\.\d+)? Tm ', element).group(0)[1:-4],
                                   "text": text_full}
                    texts_raw.append(raw_element)
            lines = [list(group) for key, group in groupby(texts_raw, key=lambda x: x["height"])]
            text = "\n".join([" ".join(i["text"] for i in line) for line in lines])
            return text

        content = search_text_blocks("Inhalte:")

        goals = search_text_blocks("Lernziele/Kompetenzen:")

        return {"title": title,
                "ects": ects,
                "content": content,
                "goals": goals}
