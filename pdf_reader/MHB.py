from dataclasses import dataclass, field
from typing import List, Dict, Union, Optional
from pdf_reader import pdf_reader_toc as prt

@dataclass(frozen=True)
class MHB:
    path: str

    content: bytes = field(init=False)
    xref_entries: List[Dict[str, str | bytes | int]] = field(init=False)
    xref_entries_filtered: List[Dict[str, int | str | bytes]] = field(init=False)
    module_codes: List[str | None] = field(init=False)
    modules: List[Dict[str, str | int | None]] = field(init=False)

    def __post_init__(self):
        modules_data = prt.Modules(pdf_path=self.path) # temporary variable used to retrieve all necessary data
        modules_data.toc_module_codes() # extracting the module codes
        object.__setattr__(self, "content", modules_data.pdf.content) # raw byte content of the pdf
        object.__setattr__(self, "xref_entries", modules_data.content) # xref_entries of pdf
        object.__setattr__(self, "xref_entries_filtered", modules_data.stream_data) # filtered xref_entries of pdf
        object.__setattr__(self, "module_codes", modules_data.module_codes) # all module codes of pdf from toc
        object.__setattr__(self, "modules", [modules_data.data_to_module(i) for i in self.module_codes]) # all modules from toc with information
        del modules_data # delete modules_data, so it can't alter data of immutable dataclass MHB

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