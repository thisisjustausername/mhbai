from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal
from pdf_reader.MHB import MHB
import numpy as np

@dataclass(frozen=True)
class Overlaps:
    # this list is also used as priority list for the order of the mhbs
    # ordered by the first MHB in the list
    # if the order doesn't matter, put the MHB with the least module_codes to the front
    mhbs: List[MHB]

    ovl_module_codes: List[str] = field(init=False)
    ovl_modules: List[Dict[str, str | None]] = field(init=False)

    @classmethod
    def input_paths(cls, paths_list: List[str]):
        return cls([MHB(path=path) for path in paths_list])

    def __post_init__(self):
        # comparing module_codes, not content (since not well cleaned, info might contain linebreaks during words adding -
        all_modules_separated = [mhb.module_codes for mhb in self.mhbs[1:]]
        shortest_mhb = np.argmin(all_modules_separated.insert(0, self.mhbs[0].module_codes))
        shortest_modules = self.mhbs[shortest_mhb].modules
        with open("mhb_overlaps.json", "w") as file:
            file.write(str(self.mhbs[shortest_mhb].content))
        object.__setattr__(self, "ovl_module_codes", [module_code for module_code in self.mhbs[0].module_codes if all(module_code in mhb for mhb in all_modules_separated)])
        object.__setattr__(self, "ovl_modules", [next((module for module in shortest_modules if module["module_code"] == module_code), None) for module_code in self.ovl_module_codes])

    def export(self, file_type: Literal["json", "csv", "xlsx", "txt", "pdf"], information: List[Literal["initial_modules", "module_code", "title", "ects", "info", "goals"]]):
        """
        def export \n
        :param file_type: chosen filetype
        :param information: chosen list of information, data is ordered by this list
        """
        if len(information) == 0:
            raise Exception("No information selected")

        data = {}
        



    def __repr__(self):
        """
                __repr__ \n
                overwrite the pretty_print function
                """
        length = max([len(i["title"]) for i in self.ovl_modules] + [0])
        return f"{', '.join(mhb.path.split('/')[-1].replace('.pdf', '') for mhb in self.mhbs)}\n     " + '\n     '.join(
            [f"{module['title']:<{length}} {module['module_code']}" for module in self.ovl_modules])


if __name__ == '__main__':
    overlaps = Overlaps.input_paths(["pdfs/Bachelor_Geographie_PO2010_ID6285_2_de_20171009_0951.pdf", "pdfs/Bachelor_Geographie_PO2010_ID6285_2_de_20171009_0951.pdf"])
    print(overlaps)