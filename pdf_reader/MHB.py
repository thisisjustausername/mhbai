# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# TODO add title to mhb, optionally other information like year etc.

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

    name: str = field(init=False)
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
        object.__setattr__(self, "name", self.path.split("/")[-1].split(".pdf")[0]) # sets the title
        object.__setattr__(self, "content", modules_data.pdf.content) # raw byte content of the pdf
        object.__setattr__(self, "xref_entries", modules_data.content) # xref_entries of pdf
        object.__setattr__(self, "xref_entries_filtered", modules_data.stream_data) # filtered xref_entries of pdf
        object.__setattr__(self, "module_codes", modules_data.module_codes) # all module codes of pdf from toc
        object.__setattr__(self, "modules", [modules_data.data_to_module(i) for i in self.module_codes]) # all modules from toc with information
        del modules_data # delete modules_data, so it can't alter data of immutable dataclass MHB

    @staticmethod
    def __json(self, data: List[Dict[str, str | int | None]],
               ordered: Annotated[bool, "Mutually exclusive with module_code_key"] = True,
               module_code_key: Annotated[bool, "Mutually exclusive with ordered"] = False, 
               name: None | str = None) -> io.StringIO:
        """
        private staticmethod def __json \n
        extracts the specified data as json
        :param data: the data, that should be converted to json
        :type data: List[Dict[str, str | int | None]]
        :param ordered: whether the data should stay ordered; mutually exclusive with module_code_key
        :type ordered: bool
        :param module_code_key: when specified, data is saved as dict with module_code as key; mutually exclusive with ordered
        :type module_code_key: bool
        :param name: name of the file
        :type name: None | str
        :return: json representation of the MHB
        :rtype: io.StringIO

        :raises ValueError: if ordered and module_code_key are specified
        """

        if ordered and module_code_key:
            raise ValueError("ordered and module_code_key are mutually exclusive")

        # in memory stream
        buffer = io.StringIO()

        json_data = dict((i["module_code"], {k: v for k, v in i.items() if k != "module_code"} )for i in data) if module_code_key else data
        json_data = {"name": name, "modules": json_data}

        json.dump(json_data, buffer, indent=3)
        
        buffer.seek(0)

        return buffer
    
    @staticmethod
    def __csv(data: List[Dict[str, str | int | None]], delimiter: Literal[";", "\t", ","], name: None | str = None) -> io.StringIO:
        """
        private staticmethod def __csv \n
        extracts the specified data as csv
        :param data: the data, that should be converted to json
        :type data: List[Dict[str, str | int | None]]
        :param delimiter: delimiter to separate the data in each row
        :type delimiter: Literal[";", "\t", ","]
        :param name: name of the file
        :type name: None | str
        :return: csv representation of the MHB
        :rtype: io.StringIO
        """

        buffer = io.StringIO()

        """write_data = [list(data[0].keys())] + [list(i.values()) for i in data]

        writer = csv.writer(buffer, delimiter=";")
        writer.writerows(write_data)"""
        writer = csv.DictWriter(buffer, fieldnames=list(data[0].keys()), delimiter=delimiter)
        writer.writeheader() if name is None else writer.writeheader(name)
        writer.writerows(data)

        buffer.seek(0)

        return buffer
    
    @staticmethod
    def __txt(data: List[Dict[str, str | int | None]], delimiter: Literal[";", "\t", ","], name: None | str = None) -> io.StringIO:
        """
        private staticmethod def __txt \n
        extracts the specified data as txt
        :param data: the data, that should be converted to txt
        :type data: List[Dict[str, str | int | None]]
        :param delimiter: the delimiter to use
        :type delimiter: Literal[";", "\t", ","]
        :param name: name of the file
        :type name: None | str
        :return: txt representation of the MHB, divided by tabs
        :rtype: io.StringIO
        """

        buffer = io.StringIO()
        if name is not None:
            buffer.write(f"{name}\n")
        write_data = [list(data[0].keys())] + [list(i.values()) for i in data]
        buffer.write("\n".join([delimiter.join(i) for i in write_data]))
        buffer.seek(0)

        return buffer
    
    @staticmethod
    def __md(data: List[Dict[str, str | int | None]], name: None | str = None, return_type: io.StringIO | str = io.StringIO) -> io.StringIO | str:
        """
        private staticmethod def __md \n
        extracts the specified data as markdown
        :param data: the data, that should be converted to markdown
        :type data: List[Dict[str, str | int | None]]
        :param name: name of the file
        :type name: None | str
        :param return_type: specify whether to return a buffer or a string
        :type: io.StringIO | str
        :return: markdown representation of the MHB as tables
        :rtype: io.StringIO | str
        """
        # since using above python 3.7 dicts stay ordered
        data_row = lambda row: f"<tr>{'\n'.join([f'<td>{str(e).replace("\n", "<br>")}</td>' for e in list(row.values())])}</tr>"

        markdown = f"<table>\n<thead>\n<tr>\n{'\n'.join([f'<th>{i}</th>' for i in data[0].keys()])}\n</tr>\n</thead>\n<tbody>\n{'\n'.join([data_row(i) for i in data])}\n</tbody>\n</table>"

        if return_type == str:
            return markdown
        markdown = f"# {name}\n" + markdown
        buffer = io.StringIO()
        buffer.write(markdown)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def __html(data: List[Dict[str, str | int | None]], name: None | str = None) -> io.StringIO:
        """
        private staticmethod def __html \n
        extracts the specified data as html
        :param data: the data, that should be converted to html
        :type data: List[Dict[str, str | int | None]]
        :param name: name of the file
        :type name: None | str
        :return: html representation of the MHB as tables
        :rtype: io.StringIO
        """

        buffer = io.StringIO()

        html = f"<!DOCTYPE html>\n<html>\n<head>\n<title>{name if name is not None else 'MHB'}</title>\n</head>\n<body>\n"
        if name is not None:
            html += f"<h1>{name}</h1>\n"
        html += f"{MHB.__md(data=data, return_type=str)}\n</body></html>"
        buffer.write(html)
        buffer.seek(0)

        return buffer

    @staticmethod
    def export_global(file_type: Literal["json", "csv", "txt", "pdf", "md", "html"], modules: List[Dict[str, str | int | None]], file_path: str | None = None,
               information: Optional[List[Literal["initial_modules", "module_code", "title", "ects", "info", "goals", "pages"]]] = None,
               ordered: bool = True, delimiter: Annotated[None | Literal[";", "\t", ","], "Mutually exclusive with the values json, pdf, md, html in file_type"] = None, 
               name: None | str = None) -> None | io.StringIO:
        """
        staticmethod export_global \n
        :param file_type: chosen filetype
        :type file_type: Literal["json", "csv", "txt", "pdf", "md", "html"]
        :param modules: if specified instead of the modules of the current MHB, the specified modules are used
        :type modules: List[Dict[str, str | int | None]]
        :param file_path: path to where to save the file to, not allowed to have file type at the end, if file_path is None, buffer will be returned
        :type file_path: str | None
        :param information: chosen list of information, data is ordered by this list
        :type information: Optional[List[Literal["initial_modules", "module_code", "title", "ects", "info", "goals", "pages"]]]
        :param ordered: whether the data should stay in order
        :type ordered: bool
        :param delimiter: delimiter to separate the data in each row; mutually exclusive with the values json, pdf, md, html in file_type
        :type delimiter: Annotated[None | Literal[";", "\t", ","], "Mutually exclusive with the values json, pdf, md, html in file_type"]
        :param name: name of the file
        :type name: None | str
        :return: buffer of the data in the correct format
        :rtype: buffer
        """

        # TODO remove this when pdf is working
        if file_type in ["pdf"]:
            raise NotImplementedError(f"{file_type} is not implemented yet.")

        if delimiter is not None and file_type not in ["csv", "txt"]:
            raise ValueError("delimiter is mutually exclusive with the values json, pdf, md, html in file_type")

        if information is not None:
            ordered_data = [{k: v for k, v in i.items() if k in information} for i in modules]
        else:
            ordered_data = modules
        

        buffer = io.StringIO()
        encoding = "utf-8"
        if file_type == "json":
            buffer = MHB.__json(ordered_data, name=name)
        else:
            ordered_data = [{k: v if type(v) != list else ", ".join([str(e) for e in v]) for k, v in i.items()} for i in ordered_data]
            if file_type == "csv":
                buffer = MHB.__csv(ordered_data, delimiter=";" if delimiter is None else delimiter, name=name)
                encoding += "-sig"
            elif file_type == "txt":
                buffer = MHB.__txt(ordered_data, delimiter=";" if delimiter is None else delimiter, name=name)
            elif file_type == "md":
                buffer = MHB.__md(ordered_data, name=name)
            elif file_type == "html":
                buffer = MHB.__html(ordered_data, name=name)
        if file_path is None:
            return buffer
        with open(f"{file_path if file_path is not None else name}.{file_type}", "w", encoding=encoding) as file:
            file.write(buffer.getvalue())
    
    def export(self, file_type: Literal["json", "csv", "txt", "pdf", "md", "html"], file_path: str | None = None,
               information: Optional[List[Literal["initial_modules", "module_code", "title", "ects", "info", "goals", "pages"]]] = None,
               ordered: bool = True, delimiter: Annotated[None | Literal[";", "\t", ","], "Mutually exclusive with the values json, pdf, md, html in file_type"] = None) -> None | io.StringIO:
        """
        export \n
        :param file_type: chosen filetype
        :type file_type: Literal["json", "csv", "txt", "pdf", "md", "html"]
        :param file_path: path to where to save the file to, not allowed to have file type at the end, if file_path is None, buffer will be returned
        :type file_path: str | None
        :param information: chosen list of information, data is ordered by this list
        :type information: Optional[List[Literal["initial_modules", "module_code", "title", "ects", "info", "goals", "pages"]]]
        :param ordered: whether the data should stay in order
        :type ordered: bool
        :param delimiter: delimiter to separate the data in each row; mutually exclusive with the values json, pdf, md, html in file_type
        :type delimiter: Annotated[None | Literal[";", "\t", ","], "Mutually exclusive with the values json, pdf, md, html in file_type"]
        :return: buffer of the data in the correct format
        :rtype: buffer
        """
        return MHB.export_global(file_type=file_type, modules=self.modules, file_path=file_path, information=information, ordered=ordered, delimiter=delimiter, name=self.name)

    def __repr__(self):
        """
        __repr__ \n
        overwrite the pretty_print function
        """
        length = max([len(i["title"]) for i in self.modules])
        return f"{self.path.split('/')[-1].replace('.pdf', '')}\n     " + '\n     '.join([f"{module['title']:<{length}} {module['module_code']}" for module in self.modules])

# TODO remove this after debugging
if __name__ == "__main__":
    path = "pdfs/Bachelor_Geographie_PO2010_ID6285_2_de_20171009_0951.pdf"
    mhb_1 = MHB(path)
    print(mhb_1)