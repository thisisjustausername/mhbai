# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.
import json
from dataclasses import dataclass, field
from typing import List, Dict, Literal, Optional, Annotated
import csv
import io
from pdf_reader import pdf_reader_toc as prt

@dataclass(frozen=True)
class MHB:
    """
    class MHB \n
    dataclass to store a single MHB
    :param path: the file_path to the pdf
    :type path: str
    """

    path: str

    content: bytes = field(init=False)
    xref_entries: List[Dict[str, str | bytes | int]] = field(init=False)
    xref_entries_filtered: List[Dict[str, int | str | bytes]] = field(init=False)
    module_codes: List[str | None] = field(init=False)
    modules: List[Dict[str, str | int | None]] = field(init=False)
    def __post_init__(self):
        """
        def __post_init__ \n
        initializes the rest of the class variables automatically
        """
        modules_data = prt.Modules(pdf_path=self.path) # temporary variable used to retrieve all necessary data
        modules_data.toc_module_codes() # extracting the module codes
        object.__setattr__(self, "content", modules_data.pdf.content) # raw byte content of the pdf
        object.__setattr__(self, "xref_entries", modules_data.content) # xref_entries of pdf
        object.__setattr__(self, "xref_entries_filtered", modules_data.stream_data) # filtered xref_entries of pdf
        object.__setattr__(self, "module_codes", modules_data.module_codes) # all module codes of pdf from toc
        object.__setattr__(self, "modules", [modules_data.data_to_module(i) for i in self.module_codes]) # all modules from toc with information
        del modules_data # delete modules_data, so it can't alter data of immutable dataclass MHB

    def __json(self, data: List[Dict[str, str | int | None]],
               ordered: Annotated[bool, "Mutually exclusive with module_code_key"] = True,
               module_code_key: Annotated[bool, "Mutually exclusive with ordered"] = False):
        """
        private def __json \n
        extracts the specified data as json
        :param data: the data, that should be converted to json
        :type data: List[Dict[str, str | int | None]]
        :param ordered: whether the data should stay ordered; mutually exclusive with module_code_key
        :type ordered: bool
        :param module_code_key: when specified, data is saved as dict with module_code as key; mutually exclusive with ordered
        :type module_code_key: bool
        :return: json representation of the MHB
        :rtype: buffer

        :raises ValueError: if ordered and module_code_key are specified
        """

        if ordered and module_code_key:
            raise ValueError("ordered and module_code_key are mutually exclusive")

        # in memory stream
        buffer = io.StringIO()

        if module_code_key:
            json.dump(dict((i["module_code"], {k: v for k, v in i.items() if k != "module_code"} )for i in data), buffer, indent=3)
        else:
            json.dump(data, buffer, indent=3)
        buffer.seek(0)

        return buffer

    def __csv(self, **kwargs):
        """
        private def __csv \n
        extracts the specified data as csv
        :param kwargs: allowed params are information, ordered
        :type kwargs: dict
        :return: csv representation of the MHB
        :rtype: csv
        """

        buffer = io.StringIO()

    def export(self, file_type: Literal["json", "csv", "txt", "pdf"],
               information: List[Literal["initial_modules", "module_code", "title", "ects", "info", "goals", "pages"]] = None,
               ordered: bool = True):
        """
        def export \n
        :param file_type: chosen filetype
        :param information: chosen list of information, data is ordered by this list
        :param ordered: whether the data should stay in order
        """
        if information is not None:
            ordered_data = [{k: v for k, v in i.items() if k in information} for i in self.modules]
        else:
            ordered_data = self.modules
        if file_type == "json":
            return self.__json()

    def __repr__(self):
        """
        __repr__ \n
        overwrite the pretty_print function
        """
        length = max([len(i["title"]) for i in self.modules])
        return f"{self.path.split('/')[-1].replace('.pdf', '')}\n     " + '\n     '.join([f"{module['title']:<{length}} {module['module_code']}" for module in self.modules])

if __name__ == "__main__":
    path = "pdfs/Bachelor_Geographie_PO2010_ID6285_2_de_20171009_0951.pdf"
    mhb_1 = MHB(path)
    print(mhb_1)