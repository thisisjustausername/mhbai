"""
This module defines the pipeline for processing XML files and storing the extracted data in a database.
"""


import json
import os
from pathlib import Path
from typing import Any
from multiprocessing import Pool

from tqdm import tqdm

from database import database as db
from .xml_to_json import xml_to_json as xtj


def get_xml_files(path_to_xml: Path) -> list[Path]:
    """
    Retrieves all XML files from the specified directory and its subdirectories.
    
    Args:
        path_to_xml (Path): The path to the directory containing XML files.
    Returns:
        list[Path]: A list of paths to the XML files found in the directory.
    """
    return list(list(path_to_xml.rglob('*.xml')))


def conversion_xml_to_json(files: list[Path]) -> list[tuple[dict[str, Any], Path]]:
    """
    Converts XML files to JSON format using multiprocessing for efficiency.
    
    Args:
        files (list[Path]): A list of paths to the XML files to convert.
    Returns:
        list[tuple[dict[str, Any], Path]]: A list of tuples containing the converted JSON data and the corresponding XML file paths.
    """
    processes = os.cpu_count()
    with Pool(processes=processes) as pool:
        return list(tqdm(
            pool.imap_unordered(xtj, files),
            total=len(files)
            )
        )


if __name__ == "__main__":
    # Initialize base data
    path_to_xml = Path(os.path.expanduser("~/mhbai/mount/StudisDaten/Modulhandbuecher/"))

    print("Collecting all XML files...")
    res = get_xml_files(path_to_xml)
    print(f"Found {len(res)} XML files.")
    print()

    print("Converting XML files to JSON...")
    result = conversion_xml_to_json(res)
    for i in result:
        with open(os.path.expanduser(f"~/mhbai/xml_processing/_temp/{str(i[1]).split('/')[-1][:-3]}.json"), "w") as f:
            json.dump(i[0], f, indent=4)
    print(result)