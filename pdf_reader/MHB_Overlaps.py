# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

from dataclasses import dataclass, field
import io
from typing import Annotated, Literal
from pdf_reader.MHB import MHB
import numpy as np

@dataclass(frozen=True)
class Overlaps:
    """
    dataclass to store the overlaps of all passed in MHBs
    
    Parameters:
        mbhs (list[MHB]): list of MHBs
    """
    # this list is also used as priority list for the order of the mhbs
    # ordered by the first MHB in the list
    # if the order doesn't matter, put the MHB with the least module_codes to the front
    mhbs: list[MHB]

    ovl_module_codes: list[str] = field(init=False)
    ovl_modules: list[dict[str, str | int | None]] = field(init=False)

    @classmethod
    def input_paths(cls, paths_list: list[str]):
        """
        alternative __init__ for passing in paths instead of MHBs

        Parameters:
            paths_list (list[str]): list of paths
        """

        return cls([MHB(path=path) for path in paths_list])

    def __post_init__(self):
        """
        initializes the rest of the class variables automatically
        """
        # comparing module_codes, not content (since not well cleaned, info might contain linebreaks during words adding -
        all_modules_separated = [mhb.module_codes for mhb in self.mhbs[1:]]
        shortest_mhb = np.argmin(all_modules_separated.insert(0, self.mhbs[0].module_codes))
        shortest_modules = self.mhbs[shortest_mhb].modules
        with open("mhb_overlaps.json", "w") as file:
            file.write(str(self.mhbs[shortest_mhb].content))
        object.__setattr__(self, "ovl_module_codes", [module_code for module_code in self.mhbs[0].module_codes if all(module_code in mhb for mhb in all_modules_separated)])
        object.__setattr__(self, "ovl_modules", [next(({k: v for k, v in module.items() if k != "pages"} for module in shortest_modules if module["module_code"] == module_code), None) for module_code in self.ovl_module_codes])

    def export(self, file_type: Literal["json", "csv", "txt", "pdf", "md", "html"], file_path: str | None = None,
               information: list[Literal["initial_modules", "module_code", "title", "ects", "info", "goals", "pages"]] | None = None,
               ordered: bool = True, delimiter: Annotated[None | Literal[";", "\t", ","], "Mutually exclusive with the values json, pdf, md, html in file_type"] = None, 
               borders: Annotated[bool, "True only works with file_types html"] = False) -> None | io.StringIO:
        """
        Parameters:
            file_type (Literal["json", "csv", "txt", "pdf", "md", "html"]): chosen filetype
            file_path (str | None): path to where to save the file to, not allowed to have file type at the end, if file_path is None, buffer will be returned
            information (list[Literal["initial_modules", "module_code", "title", "ects", "info", "goals", "pages"]] | None): chosen list of information, data is ordered by this list
            ordered (bool): whether the data should stay in order
            delimiter (Annotated[None | Literal[";", "\t", ","], "Mutually exclusive with the values json, pdf, md, html in file_type"]): delimiter to separate the data in each row; mutually exclusive with the values json, pdf, md, html in file_type
            borders (Annotated[False | True, "Only works with file_types html"]): specifies whether the table should contain borders or not
        Returns:
            buffer: buffer of the data in the correct format
        """
        
        # TODO remove this when pdf is working
        if file_type in ["pdf"]:
            raise NotImplementedError(f"{file_type} is not implemented yet.")
        
        name = ", ".join([i.title for i in self.mhbs])

        return MHB.export_global(file_type=file_type, file_path=file_path, information=information, ordered=ordered, delimiter=delimiter, modules=self.ovl_modules, name=name, borders=borders)

    def __repr__(self):
        """
        overwrite the pretty_print function
        """

        length = max([len(i["title"]) for i in self.ovl_modules] + [0])
        return f"{', '.join(mhb.path.split('/')[-1].replace('.pdf', '') for mhb in self.mhbs)}\n     " + '\n     '.join(
            [f"{module['title']:<{length}} {module['module_code']}" for module in self.ovl_modules])

# TODO remove this after debugging
if __name__ == '__main__':
    overlaps = Overlaps.input_paths(["pdfs/Bachelor_Geographie_PO2010_ID6285_2_de_20171009_0951.pdf", "pdfs/Bachelor_Geographie_PO2010_ID6285_2_de_20171009_0951.pdf"])
    print(overlaps)