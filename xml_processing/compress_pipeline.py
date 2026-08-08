"""
Pipeline for compressing the extended JSON study program schemas into smaller schemas more suitable for RAG.
"""

# TODO: check parts for errors, as it is always empty and doesn't seem to exist in the uni-a_mhbs_json folder files

import json
import os
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
from pathlib import Path
from typing import Any

from tqdm import tqdm

from xml_processing.compress_json import json_to_compressed_json as jcj
from xml_processing.pipeline import get_files


def conversion_json_to_json(files: list[Path] | list[tuple[Path, int]]) -> list[tuple[dict[str, Any], Path]]:
    """
    Converts JSON files to a compressed format using multiprocessing for efficiency.

    Args:
        files (list[Path] | list[tuple[Path, int]]): A list of paths to the JSON files to convert.
    Returns:
        list[tuple[dict[str, Any], Path]]: A list of tuples containing the converted JSON data and the corresponding JSON file paths.
    """
    processes = os.cpu_count()
    with Pool(processes=processes) as pool:
        return list(tqdm(
            pool.imap_unordered(jcj, files),
            total=len(files)
            )
        )

def save(res) -> None:
    """
    Saves the given data to a JSON file at the specified path.

    Args:
        data (dict[str, Any]): The data to save.
        file_path (Path): The path where the JSON file will be saved.
    """
    name = res[1][0].stem + '__' + str(res[1][1]) + '.json'
    with open(Path(os.path.expanduser(f"~/mhbai/ai/compressed_mhbs/{name}")), "w") as f:
        json.dump(res[0], f, indent=4)


def save_concurrently(results):
    """
    Saves the converted JSON data to files concurrently using a thread pool.

    Args:
        results (list[tuple[dict[str, Any], Path]]): A list of tuples containing the converted JSON data and the corresponding file paths.
    """
    processes = os.cpu_count()
    with ThreadPoolExecutor(max_workers=processes) as executor:
        executor.map(save, results)


if __name__ == "__main__":
    # Initialize base data
    str_path = "~/mhbai/uni-a_mhbs_json/"
    path_to_json = Path(os.path.expanduser(str_path))

    print("Collecting all JSON files...")
    res = get_files(path_to_json, file_type="json")
    res: list[tuple[Path, int]] = [(r, index) for index, r in enumerate(res)]
    with open(Path(os.path.expanduser("~/mhbai/ai/compressed_mhbs/metadata.json")), "w") as f:
        json.dump([(str(r[0]), r[1]) for r in res], f, indent=4)
    print(f"Found {len(res)} JSON files.")
    print()

    print("Converting JSON files...")
    result = conversion_json_to_json(res)
    print()
    print("Saving converted JSON files...")
    save_concurrently(result)
