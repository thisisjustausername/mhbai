"""
This module defines the pipeline for processing XML files and storing the extracted data in JSON files.
"""

# TODO: evaluate the exact cause why concurrent saving droppend around 3000 / 26000 files here

import json
import os
from multiprocessing import Pool
from pathlib import Path
from typing import Any

from tqdm import tqdm

from .xml_to_json import xml_to_json as xtj


def get_files(path_to_file: Path, file_type: str = "xml") -> list[Path]:
    """
    Retrieves all XML files from the specified directory and its subdirectories.

    Args:
        path_to_file (Path): The path to the directory containing files.
        file_type (str): The type of files to retrieve (default is "xml").
    Returns:
        list[Path]: A list of paths to the files found in the directory.
    """
    return list(path_to_file.rglob(f'*.{file_type}'))


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


def save(res: tuple[dict, Path]) -> None:
    """
    Saves the given data to a JSON file at the specified path.

    Args:
        res (tuple[dict, Path]): The data to save.
        file_path (Path): The path where the JSON file will be saved.
    """
    with open(Path(os.path.expanduser(f"~/mhbai/xml_processing/_temp/{res[1].stem}.json")), "w") as f:
        json.dump(res[0], f, indent=4)


if __name__ == "__main__":
    # Initialize base data
    path_to_xml = Path(os.path.expanduser("~/mhbai/mount/StudisDaten/Modulhandbuecher/"))

    print("Collecting all XML files...")
    res = get_files(path_to_xml)
    print(f"Found {len(res)} XML files.")
    print()

    print("Converting XML files to JSON...")
    result = conversion_xml_to_json(res)

    print()
    print("Saving converted JSON files...")
    # save_concurrently(result)
    for res in tqdm(result):
        save(res)
