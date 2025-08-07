# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# TODO add title to mhb, optionally other information like year etc.

import json
from dataclasses import dataclass, field, replace
from typing import Literal, Annotated, Type
from typing import get_type_hints
import csv
import io
from pdf_reader import pdf_reader_toc as prt
from pdf_reader.Type_Checker import type_check

@dataclass(frozen=True)
class MHB:
    """
    dataclass to store a single MHB

    Parameters:
        path (str): the file_path to the pdf
    """

    path: str

    name: str = field(init=False)
    content: bytes = field(init=False)
    xref_entries: list[dict[str, str | bytes | int]] = field(init=False)
    xref_entries_filtered: list[dict[str, int | str | bytes]] = field(init=False)
    module_codes: list[str] = field(init=False)
    modules: list[dict[str, str | int | None]] = field(init=False)
    title: str = field(init=False)

    def __post_init__(self):
        """
        initializes the rest of the class variables automatically
        """
        modules_data = prt.Modules(pdf_path=self.path) # temporary variable used to retrieve all necessary data
        modules_data.toc_module_codes() # extracting the module codes
        object.__setattr__(self, "name", self.path.split("/")[-1].split(".pdf")[0]) # sets the name using the name of the pdf (can act as id)
        object.__setattr__(self, "content", modules_data.pdf.content) # raw byte content of the pdf
        object.__setattr__(self, "xref_entries", modules_data.content) # xref_entries of pdf
        object.__setattr__(self, "xref_entries_filtered", modules_data.stream_data) # filtered xref_entries of pdf
        object.__setattr__(self, "module_codes", modules_data.module_codes) # all module codes of pdf from toc
        object.__setattr__(self, "modules", [modules_data.data_to_module(i) for i in self.module_codes]) # all modules from toc with information
        object.__setattr__(self, "title", modules_data.title()) # set the name of the mhb (extracted from pdf)
        del modules_data # delete modules_data, so it can't alter data of immutable dataclass MHB

    @classmethod
    # @type_check
    def init_manually(cls, path: str, title: str, name: str, module_codes: list[str], modules: list[dict[str, str | int | None]]):
        """
        initializes MHB manually, used for creating an MHB from saved data

        Parameters:
            path (str): the file_path to the pdf
            title (str): the title of the MHB
            name (str): the name of the MHB, used as id
            module_codes (list[str]): the module codes of the MHB
            modules (list[dict[str, str | int | None]]): the modules of the MHB
        """
        obj = cls.__new__(cls)

        object.__setattr__(obj, "path", path)
        object.__setattr__(obj, "title", title)
        object.__setattr__(obj, "name", name)
        object.__setattr__(obj, "module_codes", module_codes)
        object.__setattr__(obj, "modules", modules)

        return obj

    @staticmethod
    # @type_check
    def __json(data: list[dict[str, str | int | None]],
               ordered: Annotated[bool, "Mutually exclusive with module_code_key"] = True,
               module_code_key: Annotated[bool, "Mutually exclusive with ordered"] = False, 
               name: None | str = None) -> io.StringIO:
        """
        extracts the specified data as json

        Parameters:
            data (list[dict[str, str | int | None]]): the data, that should be converted to json
            ordered (bool): whether the data should stay ordered; mutually exclusive with module_code_key
            module_code_key (bool): when specified, data is saved as dict with module_code as key; mutually exclusive with ordered
            name (None | str): name of the file
        Returns:

            :: io.StringIO: json representation of the MHB
            ValueError: if ordered and module_code_key are specified
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
    # @type_check
    def __csv(data: list[dict[str, str | int | None]], delimiter: Literal[";", "\t", ","], name: None | str = None) -> io.StringIO:
        """
        extracts the specified data as csv

        Parameters:
            data (list[dict[str, str | int | None]]): the data, that should be converted to json
            delimiter (Literal[";", "\t", ","]): delimiter to separate the data in each row
            name (None | str): name of the file
        Returns:io.StringIO: csv representation of the MHB
        """
        buffer = io.StringIO()
        
        """write_data = [list(data[0].keys())] + [list(i.values()) for i in data]

        writer = csv.writer(buffer, delimiter=";")
        writer.writerows(write_data)"""
        writer = csv.DictWriter(buffer, fieldnames=list(data[0].keys()), delimiter=delimiter)
        
        # TODO test, whether this works as intended
        if name is not None:
            buffer.write(f"{name}\n")
        
        writer.writeheader()
        writer.writerows(data)

        buffer.seek(0)

        return buffer
    
    @staticmethod
    # @type_check
    def __txt(data: list[dict[str, str | int | None]], delimiter: Literal[";", "\t", ","], name: None | str = None) -> io.StringIO:
        """
        extracts the specified data as txt

        Parameters:
            data (list[dict[str, str | int | None]]): the data, that should be converted to txt
            delimiter (Literal[";", "\t", ","]): the delimiter to use
            name (None | str): name of the file
        Returns:
            io.StringIO: txt representation of the MHB, divided by tabs
        """
        buffer = io.StringIO()
        if name is not None:
            buffer.write(f"{name}\n")
        write_data = [list(data[0].keys())] + [list(i.values()) for i in data]
        buffer.write("\n".join([delimiter.join(str(i)) for i in write_data]))
        buffer.seek(0)

        return buffer
    
    @staticmethod
    # @type_check
    def __md(data: list[dict[str, str | int | None]], name: None | str = None, return_type: Type[io.StringIO] | Type[str] = io.StringIO, borders: Annotated[bool, "True is mutually exclusive with return_type = io.StringIO"] = False) -> io.StringIO | str:
        """
        extracts the specified data as markdown

        Parameters:
            data (list[dict[str, str | int | None]]): the data, that should be converted to markdown
            name (None | str): name of the file
            return_type (| str): specify whether to return a buffer or a string
            borders: specifies (| True, "True is mutually exclusive with return_type = io.StringIO"]) whether the table should contain borders or not
        Returns:
            io: markdown representation of the MHB as tables
        """

        if return_type is io.StringIO and borders:
            raise ValueError("borders = True is mutually exclusive with return_type = io.StringIO")

        # since using above python 3.7 dicts stay ordered
        data_row = lambda row: f"<tr>{'\n'.join([f'<td>{str(e).replace("\n", "<br>")}</td>' for e in list(row.values())])}</tr>"

        markdown = f'<table {'border="1"' if borders else ''}>\n<thead>\n<tr>\n{'\n'.join([f'<th>{i}</th>' for i in data[0].keys()])}\n</tr>\n</thead>\n<tbody>\n{'\n'.join([data_row(i) for i in data])}\n</tbody>\n</table>'

        if return_type is str:
            return markdown
        markdown = f"# {name}\n" + markdown
        buffer = io.StringIO()
        buffer.write(markdown)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    # @type_check
    def __html(data: list[dict[str, str | int | None]], name: str, borders: bool = False) -> io.StringIO:
        """
        private staticmethod def __html \n
        extracts the specified data as html
            data (list[dict[str, str | int | None]]): the data, that should be converted to html
            name (str): name of the file
            borders: specifies whether the table should contain borders or not
        :type ( html representation of the MHB as tables): bool
        :rtype: io.StringIO
        """

        buffer = io.StringIO()

        html = f"<!DOCTYPE html>\n<html>\n<head>\n<title>{name}</title>\n</head>\n<body>\n"
        html += f"<h1>{name}</h1>\n"
        html += f"{MHB.__md(data=data, return_type=str, borders=borders)}\n</body></html>"
        buffer.write(html)
        buffer.seek(0)

        return buffer

    @staticmethod
    # @type_check
    def export_global(file_type: Literal["json", "csv", "txt", "pdf", "md", "html"], modules: list[dict[str, str | int | None]], name: str, file_path: str | None = None,
               information: list[Literal["initial_modules", "module_code", "title", "ects", "info", "goals", "pages"]] | None = None,
               ordered: bool = True, delimiter: Annotated[None | Literal[";", "\t", ","], "Mutually exclusive with the values json, pdf, md, html in file_type"] = None, 
               borders: Annotated[bool, "True only works with file_types html"] = False) -> None | io.StringIO:
        """
        staticmethod to extract data
        Parameters:
            file_type (Literal["json", "csv", "txt", "pdf", "md", "html"]): chosen filetype
            modules (list[dict[str, str | int | None]]): if specified instead of the modules of the current MHB, the specified modules are used
            name (str): name of the file
            file_path (str | None): path to where to save the file to, not allowed to have file type at the end, if file_path is None, buffer will be returned
            information (list[Literal["initial_modules", "module_code", "title", "ects", "info", "goals", "pages"]] | None): chosen list of information, data is ordered by this list
            ordered (bool): whether the data should stay in order
            delimiter (Annotated[None | Literal[";", "\t", ","], "Mutually exclusive with the values json, pdf, md, html in file_type"]): delimiter to separate the data in each row; mutually exclusive with the values json, pdf, md, html in file_type
            borders: specifies (| True, "Only works with file_types html"] = False) whether the table should contain borders or not
        Returns:
            buffer: buffer of the data in the correct format
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
            buffer = MHB.__json(data=ordered_data, name=name)
        else:
            ordered_data = [{k: v if type(v) != list else ", ".join([str(e) for e in v]) for k, v in i.items()} for i in ordered_data] # type: ignore[reportGeneralTypeIssues]
            if file_type == "csv":
                buffer = MHB.__csv(ordered_data, delimiter=";" if delimiter is None else delimiter, name=name)
                encoding += "-sig"
            elif file_type == "txt":
                buffer = MHB.__txt(ordered_data, delimiter=";" if delimiter is None else delimiter, name=name)
            elif file_type == "md":
                buffer = MHB.__md(ordered_data, name=name, borders=borders)
            elif file_type == "html":
                buffer = MHB.__html(ordered_data, name=name, borders=borders)
        if file_path is None:
            return buffer # type: ignore[ReportReturnType]
        with open(f"{file_path}.{file_type}", "w", encoding=encoding) as file:
            file.write(buffer.getvalue()) # type: ignore[ReportReturnType]
    
    # @type_check
    def export(self, file_type: Literal["json", "csv", "txt", "pdf", "md", "html"], file_path: str | None = None,
               information: list[Literal["initial_modules", "module_code", "title", "ects", "info", "goals", "pages"]] | None = None,
               ordered: bool = True, delimiter: Annotated[None | Literal[";", "\t", ","], "Mutually exclusive with the values json, pdf, md, html in file_type"] = None, 
               borders: Annotated[bool, "True only works with file_types html"] = False) -> None | io.StringIO:
        """
        extract data from current MHB
        Parameters:
            file_type (Literal["json", "csv", "txt", "pdf", "md", "html"]): chosen filetype
            file_path (str | None): path to where to save the file to, not allowed to have file type at the end, if file_path is None, buffer will be returned
            information (list[Literal["initial_modules", "module_code", "title", "ects", "info", "goals", "pages"]] | None): chosen list of information, data is ordered by this list
            ordered (bool): whether the data should stay in order
            delimiter (Annotated[None | Literal[";", "\t", ","], "Mutually exclusive with the values json, pdf, md, html in file_type"]): delimiter to separate the data in each row; mutually exclusive with the values json, pdf, md, html in file_type
            borders: specifies (| True, "Only works with file_types html"]) whether the table should contain borders or not
        Returns:
            buffer: buffer of the data in the correct format
        """
        return MHB.export_global(file_type=file_type, modules=self.modules, file_path=file_path, information=information, ordered=ordered, 
                                 delimiter=delimiter, name=self.title, borders=borders)

    def __repr__(self):
        """
        overwrite the pretty_print function
        """
        length = max([len(i["title"]) for i in self.modules]) # type: ignore[reportArgumentType]
        return f"{self.path.split('/')[-1].replace('.pdf', '')}\n     " + '\n     '.join([f"{module['title']:<{length}} {module['module_code']}" for module in self.modules])

# TODO remove this after debugging
if __name__ == "__main__":
    path = "pdfs/Bachelor_Geographie_PO2010_ID6285_2_de_20171009_0951.pdf"
    mhb_1 = MHB(path)
    print(mhb_1)