# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai and pdf_reader.
#
# For usage please contact the developer.

from pdf_reader import pdf_extractor as extr
import re
from itertools import groupby
from typing import Optional, List

# TODO cleanly comment this code
def find_title(split_line: str, title_search_lines: list) -> Optional[tuple]:
    """
    find_title \n
    helper function to extract title from a specific search window
    :param split_line: the part to split, e.g. english title or end of box
    :type split_line: str
    :param title_search_lines: search windows split into lines
    :type title_search_lines: list
    :return: title, local index of the end of the title
    :rtype: Optional[str, int]
    """
    if not any([split_line == i for i in title_search_lines]):  # false, when split_line was found
        return None
    # shrink window
    # set indexer to -1 so it is clear when nothing was found
    indexer = -1
    # enumerate through lines and if match is found break and save to indexer
    for index, i in enumerate(title_search_lines):
        if i == split_line:
            indexer = index
            break
    if not indexer != -1:  # checks whether window shrink was successful (this is unnecessary, since always false, but for failsave)
        return None

    # save the local index of the end of the title, so it can be added to the global offset to get the position from where on ects etc. will be searched
    local_end_index = len("\n".join(title_search_lines[:indexer])) + 1  # plus new line
    title_search_lines = title_search_lines[:indexer] # lines to search in for title
    title_list = [] # contains all title matches
    is_gray = False # if something is written in gray it is an alternative title / module, so it can be ignored

    # this iteration collects the whole title, also when it spans over multiple lines
    # enumerate through lines, that may contain title
    for index, i in enumerate(title_search_lines):
        if re.match(r'\d+(?:\.\d+)? g', i): # pattern for start gray writing
            is_gray = True
        elif re.match(r'0 0 1 rg', i): # pattern for end gray writing
            is_gray = False
        if not is_gray:
            pattern = r'\[\(.*?\)\]' if index != 0 else r'.*?\)\]' # pattern for a part of the title
            match = re.search(pattern, i)
            if match is not None:
                # if title is found, add rawly cleaned part of title
                # depending on whether the title is in the first line or another, clean it differently
                cleaned = match.group(0)[:-2] if index == 0 and not match.group(0).startswith("[(") else \
                match.group(0).split("[(", 1)[1][:-2]
                title_list.append(cleaned)

    # removes hyphen from the end of line when a word is separated into two lines
    clean_titles = []
    for index, i in enumerate(title_list):
        if index == len(title_list) - 1:
            clean_titles.append(i)
        # if title was separated mid-word then remove hyphen
        elif i.endswith("-") and title_list[index + 1][0].islower():
            clean_titles.append(i[:-1])
        else:
            clean_titles.append(i + " ")
    # add all parts of the title to one string
    title = "".join(clean_titles)[2:]
    # return title and the index of the local end of the title
    return title, local_end_index


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
        self.module_codes: list = []
        # NOTE enable this to extract page numbers from toc, version 2.0
        # self.module_codes_detailed: list = []


    def toc_module_codes(self):
        """
        def toc_module_codes \n
        :return list of module_codes
        :rtype List[str]
        """
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
        # NOTE rather use this when using page_numbers version2.0 for checking (maybe not implemented yet)
        # matches = [i for i in matches]
        # split matches in lines
        # not sorting so that just lines that are together are packed together in order to not ignore page breaks
        #matches.sort(key=lambda x: x[1])
        lines = [list(group) for key, group in groupby(matches, key=lambda x:x[1])]
        # probably not anymore: in the current code page breaks are ignored. this creates the error of mixing module codes, that are on the same height but on different pages. Fix it by either not ignoring line breaks or making it a different height, when between it is a different height, e.g. by not sorting list before grouping it
        # get page number and module code
        modules = []
        # NOTE enable this to extract page numbers from toc, version 2.0
        # modules_detailed = []
        # TODO if the page number is in the next line, still take it
        # for now simply ignore page number
        for line_index, line in enumerate(lines): # go through every line
            # is_module = False # if module code is found set to true NOTE uncomment if using page numbers
            # module = [] NOTE uncomment if using page numbers
            for index, part in enumerate(line): # for every part in the line, check whether it is a module code
                # NOTE uncomment if using page numbers
                # if not is_module:  # if it is not the first module code, then ignore it
                code = re.search(r' Tm \[\([A-ZÄÖÜ]{2,}-\d{3,}', part[0])
                if code is not None: # if module code is found, execute this
                    # NOTE enable this to extract page numbers from toc, version 2.0
                    """
                    # dirty code but it extracts page numbers of modules, if the page number is in the same or up to two lines below the module code
                    page_nr_index = line_index
                    dot = " Tm [(.)"
                    if dot in line[-1]:
                        if dot in lines[line_index + 1] and len([True for i in lines[line_index + 1] if re.search(r' Tm \[\([A-ZÄÖÜ]{2,}-\d{3,}', i[0]) is not None]) == 0:
                            page_nr_index += 1
                        elif dot in lines[line_index + 2] and len([True for i in lines[line_index + 2] if re.search(r' Tm \[\([A-ZÄÖÜ]{2,}-\d{3,}', i[0]) is not None]) == 0:
                            page_nr_index += 2
                        else:
                            page_nr_index = -1
                    page_nr = None
                    if page_nr_index != -1:
                        page_nr_match = re.search(r'\[\(\d+\)', lines[page_nr_index][-1][0])
                        if page_nr_match is not None:
                            page_nr = int(page_nr_match.group(0)[2:-1])
                    """
                    # NOTE uncomment if using page numbers
                    # is_module = True # set module code to True
                    modules.append(code.group(0)[6:])
                    # NOTE enable this to extract page numbers from toc, version 2.0
                    # modules_detailed.append({"module_code": code.group(0)[6:], "page_nr": page_nr})

                    # module.append(code.group(0)[6:-2]) # append the code to the module list NOTE uncomment if using page numbers
                    break # NOTE comment this if using page numbers, version 1.0 and 2.0
                # ignore page number
                # NOTE when uncommenting do this: if the page number is in the next line, still take it
                r"""else: # if a module code was already found, then search for page numbers
                    page_number = re.search(r' Tm \[\(\d+\)\]', part[0]) # search for page number
                    if page_number is not None: # if page number was found, execute this
                        module.append(page_number.group(0)[6:-2]) # add page number to module list
            if len(module) > 2: # if the module contains more than one page number, just keep the last one
                module = [module[0], module[-1]]"""
        # remove duplicates, but keeping the order
        seen_set = set()
        new_mods = []
        for i in modules:
            if not i in seen_set:
                seen_set.add(i)
                new_mods.append(i)
        modules = new_mods

        # set class vars and return modules
        self.module_codes = modules
        # NOTE enable this to extract page numbers from toc, version 2.0
        # self.module_codes_detailed = modules_detailed
        return modules #, modules_detailed NOTE enable this to extract page numbers from toc, version 2.0


    # TODO in order to make the program more efficient, when finding all title pages already save them for extracting ects etc. instead of searching them again
    def data_to_module(self, module_code: str) -> Optional[dict]:
        """
        data_to_module \n
        :param module_code: module code of the module, that should be searched
        :type module_code: str
        :return: information to the module
        :rtype: Optional[Dict[str, str | int | None]]
        """
        # TODO alternative way of extracting page numbers, extract page number of every page that has the module in the head
        # if no module_codes were extracted, extract them first
        if self.module_codes is None:
            self.toc_module_codes()

        # set default title start
        # IMPORTANT can be removed, simply affects ects since in title extraction it is just being used when no error occurred thus it exists
        title_start = 0

        # if the current pdf doesn't contain passed in module_code, return None
        # TODO rather than returning None maybe throw Exception
        if module_code not in self.module_codes:
            return None

        # all pages that mentions the module
        matching_pages = [page for page in self.stream_data if re.search(r'Modul ' + module_code, page) is not None]

        # find the first page that has the module in the heading signature
        error = True
        page_index = None
        correct_pages = [page for page in self.stream_data if re.search(r'Tm \[\(Modul ' + module_code, page) is not None]
        page_nr_list = []
        for i in correct_pages:
            # match = re.search(r' Tm \[\(\d+\)\] TJ\nET\nQ\nQ', i)
            match = list(re.finditer(r' Tm \[\(\d+\)\] TJ\nET\nQ\nQ', i))[-1]
            page_nr_list.append(match.group(0)[6:-12] if match is not None else None)
        page_nr_list = [int(i) for i in page_nr_list]
        for index, match_page in enumerate(matching_pages):
            # e.g. module is not found if it was mentioned in the chapter of another module
            try:
                titles = re.finditer(r'Tm \[\(Modul ' + module_code, matching_pages[index])
                titles_list = list(re.finditer(r'Tm \[\(Modul ' + module_code, matching_pages[index]))
                title_start = [i for i in titles if len(matching_pages[index][i.start()-100: i.start()].split("\n")) > 1 and "/F3 10" in matching_pages[index][i.start()-100: i.start()].split("\n")[-2]][0].end()
                error = False
                page_index = index
                break
            except:
                pass
        # if no page was found, set the title to None
        if error:
            title = None
        else:
            # create a search window around the found title
            title_search = matching_pages[page_index][title_start:title_start+700]
            # if module_code == "GEO-2043":
            title_search_lines = title_search.split("\n") # split search window into lines

            # no need to check, whether end of box ET or engl title is earlier, since engl title seq doesn't exist near after ET
            # if english title is found, shrink title window until this begins
            engl_title_seq = '/F2 9 Tf'
            result = find_title(engl_title_seq, title_search_lines) # try to find english title
            # if english title exists, then set title
            if result is not None:
                title = result[0]
                start_info = result[1] + title_start
            else: # if no english title exists shrink search window to the end of the cell
                end_of_box = "ET"
                result = find_title(end_of_box, title_search_lines)
                # search again for the title
                if result is not None:
                    title = result[0]
                    start_info = result[1] + title_start
                else: # if no title was found, simply use title pattern for title
                    title_raw = re.search(r': [^\]]+\)\] TJ', title_search)
                    if title_raw is None:
                        title = None
                    else:
                        title = title_raw.group(0)[2:].split(")]")[-2]
                        start_info = title_raw.end() + title_start  # doesn't it have to be plus title_start

        # if title was found, do further cleaning
        if title is not None:
            # check whether LP information is in the title
            pattern_list = [r'\\\(\d+LP\\\)', r' \\\(\d+ LP\\\)', r' \d+ CP$']

            title_match = re.search(pattern_list[0], title)
            if title_match is None:
                title_match = re.search(pattern_list[1], title)
                if title_match is None:
                    title_match = re.search(pattern_list[2], title)
            if title_match is not None:
                title = title[:title_match.start()] + " " + title[title_match.end():]
            # further LP extraction
            else:
                # match = re.search(r' \\\(.*\d+ LP.*\\\)', title)
                partly_pattern_list = [r'[;,] \d+ LP\\\)', r' \d+ LP\\\)']
                match = re.search(r' \\\(\d+ LP[;,] ', title)
                if match is not None:
                    title = title[:match.start()+3] + title[match.end():]
                else:
                    for pattern in partly_pattern_list:
                        match = re.search(pattern, title)
                        if match is not None:
                            title = title[:match.start()] + title[match.end()-3:]
                            break
        title = title.strip()
        title = re.sub(r'\s+', ' ', title)
        title = title.encode('utf-8').decode('unicode_escape')
        title = title.replace("\\", "")


        # TODO if no ects but everything else available, simply set ects to None
        # TODO when no title was found, then set a default start_info index
        try:
            ects = int(re.search(r' Tm \[\(\d+ ECTS/LP\)\] TJ', matching_pages[page_index][start_info:]).group(0).split("Tm [(", 1)[1].split("ECTS", 1)[0])
        except:
            ects = None

        def search_text_blocks(heading: str) -> str:
            """
            inside function search_text_blocks \n
            This function extracts text blocks for a specific heading in a module (e.g. Inhalt in a module) \n
            This only works when the box doesn't contain any subcells from the table
            :param heading: string to search for e.g. Inhalte:
            :type heading: str
            :return: the text block
            """

            information = [page[start_info:] for page in matching_pages] # shrink search window
            details_list = [] # save cells with information in it in details_list
            # extracts all cells, that have the desired heading
            for page in information:
                # for each page search for the heading
                start = re.search(r' Tm \[\(' + heading + r'\)\] TJ', page)
                if start is None:
                    continue
                start = start.start()
                end = re.search(r'\nET\nQ', page[start:]).start() # end of the cell
                details_list.append(page[start:start + end])

            # extract the text out of each block
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
            # groups all blocks and combines them with "\n"
            lines = [list(group) for key, group in groupby(texts_raw, key=lambda x: x["height"])]
            text = "\n".join([" ".join(i["text"] for i in line) for line in lines])
            return text

        # extract the info description of a module
        try:
            content = search_text_blocks("Inhalte:")
        except:
            content = None

        # extract the goals of a module
        try:
            goals = search_text_blocks("Lernziele/Kompetenzen:")
        except:
            goals = None

        # Hi, is someone reading me?
        # Will anyone ever read this? (yes|no|maybe)

        # return a dictionary of title, module_code, ects, content, goals and pages
        detailed_dict = {"title": title,
                        "module_code": module_code.encode('utf-8').decode('unicode_escape'),
                        "ects": ects,
                        "content": content.encode('utf-8').decode('unicode_escape'),
                        "goals": goals.encode('utf-8').decode('unicode_escape'),
                        "pages": page_nr_list,
                        "mhbai_hints": None}
        # NOTE enable this if validation of page_nrs with toc is wished
        """
        toc_page_nr = [i for i in self.module_codes_detailed if i["module_code"] == module_code][0]["page_nr"]
        if min(page_nr_list) != toc_page_nr:
        detailed_dict["mhbai_hints"] = f"Pages of module information ({', '.join([str(i) for i in page_nr_list])}) don't match page number ({str(toc_page_nr)}) in table of content "
        """
        return detailed_dict