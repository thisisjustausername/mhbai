import json
import os
from pathlib import Path
from typing import Any
from multiprocessing import Pool

from tqdm import tqdm

from database import database as db
from .xml_to_json import xml_to_json as xtj


def get_json_files(path_to_json: Path) -> list[Path]:
    """
    Retrieves all JSON files from the specified directory and its subdirectories.

    Args:
        path_to_json (Path): The path to the directory containing JSON files.
    Returns:
        list[Path]: A list of paths to the JSON files found in the directory.
    """
    return list(list(path_to_json.rglob('*.json')))

if __name__ == "__main__":
    # Initialize base data
    path_to_json = Path(os.path.expanduser("~/mhbai/uni-a_mhbs_json/"))

    print("Collecting all JSON files...")
    res = get_json_files(path_to_json)
    print(f"Found {len(res)} JSON files.")
    print()

    for i in res:
        with open(i, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data is None:
            continue
        for e in data.get("module_groups", []):
            for j in e.get("modules", []):
                for k in j.get("exams", []):
                    mapping = k.get("module_course_exams", None)
                    if isinstance(mapping, list) and len(mapping) > 0:
                        print(mapping)