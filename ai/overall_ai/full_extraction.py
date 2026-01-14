# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# For usage please contact the developer.
#
# This file is Copyright-protected.

# Description: extract modules from module handbooks and extract data from these models as well as store the data
# Status: IN DEVELOPMENT
# FileID: Ai-ex-0002

"""
extract modules from module handbooks
extract data from these models
store the data in a database
"""

import math
import json
import os
import multiprocessing
from typing import Any
from tqdm import tqdm
from psycopg2.extras import Json

from database import database as db
from ai.overall_ai.data_extraction import extract_module_info as emi
from pdf_reader import pdf_reader_toc as prt
from datatypes.result import Result


def extract_modules_from_files(files: list[str]) -> set[tuple[str, Any]]:
    """
    extracts raw module data from mhbs

    Args:
        files (list[str]): mhbs as pdfs to extract the raw modules from

    Returns:
        set[tuple[str, Any]]: set of modules, each module is made up of two tuples:
                              (("module_code", <module_code>), ("content": <content>))
    """
    # create a set to store unique modules
    modules_set = set()

    # extract modules from each file
    for file in files:
        # try creating Modules object
        try:
            modules: prt.Modules = prt.Modules(pdf_path=file)
        except Exception:
            print(f"Error processing file {file}")
            continue
        # get raw module text pages from Modules object
        modules_raw = modules.raw_module_texts()

        # remove duplicates
        modules_set.update(set(tuple(i.items()) for i in modules_raw))  # type: ignore

    return modules_set  # type: ignore


def save_to_db(cursor, module: dict[str, Any]) -> bool:
    """
    save extracted module data to database

    Args:
        cursor: database cursor
        module (list[dict[str, Any]]): list of extracted module data
    """
    result = db.insert(
        cursor=cursor,
        table="unia.modules_ai_extracted",
        values=module,
        returning_column="id",
    )
    if result.is_error:
        return False
    return True


@db.cursor_handling(manually_supply_cursor=False)
def load_pdf_modules(
    pdf_folder: str, save_path: str | None = None, from_db: bool = True, cursor=None
) -> list[dict[str, Any]]:
    """
    load all raw modules from all pdfs in a folder
    remove duplicates on the way in order to keep the ai data extraction time minimal

    Args:
        pdf_folder (str): folder path where the pdfs are located
        save_path (str | None): optional path to save the raw modules as json file
                                if not specified, data won't be saved persistently;
                                If save_path == "": then data will be saved to DATABASE
        from_db (bool): True when loading data from db, False when computing data freshly
        cursor: specified by decorator

    Returns:
        list[dict[str, Any]]: list of dictionaries, each containing a module code and the matching
        content. Note: module codes can exist more than once, since multiple versions of a module
        exist (each module has around 16 different versions)
    """

    if from_db is True:
        result = db.select(
            cursor=cursor,  # type: ignore
            table="unia.raw_modules",
            keywords=["id", "module_code", "content"],
        )
        if result.is_error:
            raise Exception("Error occurred while reading data from the database")
        return result.data

    # expand path
    pdf_folder = os.path.expanduser(pdf_folder)

    # fetch all mhb pdfs from folder
    files = [
        os.path.join(pdf_folder, f)
        for f in os.listdir(pdf_folder)
        if os.path.isfile(os.path.join(pdf_folder, f)) and f.endswith(".pdf")
    ]

    # extract raw modules from each file
    print(f"Extracting raw module data from {len(files)} mhbs.")
    modules_set = set()

    # with multiprocessing
    cpu_count = multiprocessing.cpu_count()
    urls_per_job = math.ceil(len(files) / cpu_count)

    with multiprocessing.Pool(processes=cpu_count) as pool:
        results = [
            pool.apply_async(
                extract_modules_from_files, args=(files[i : i + urls_per_job],)
            )
            for i in range(0, len(files), urls_per_job)
        ]
        for result in results:
            data = result.get()
            modules_set.update(data)

    modules = list(dict(i) for i in modules_set)
    if save_path is not None and save_path != "":
        with open(os.path.expanduser(save_path), "w", encoding="utf-8") as file:
            json.dump(modules, file, indent=4)

    if from_db is False and save_path == "":
        result = save_raw(modules)
        if result.is_error:
            print(result.error)
            raise Exception("Error saving data to database")
        # add ids to modules
        modules = [{"id": id_, **module} for id_, module in zip(result.data, modules)]
    return modules


@db.cursor_handling(manually_supply_cursor=False)
def save_raw(raw_modules: list[dict[str, str]], cursor=None) -> Result:
    """
    saves the raw module data to db

    Args:
        raw_modules (list[dict[str, str]]): dictionary with raw module data: module_code: str, content: str
        cursor: specified by decorator

    Returns:
        Result: Result object indicating success or error
    """
    query = f"""INSERT INTO unia.modules_raw (module_code, content)
               VALUES {', '.join(['%s' for i in range(len(raw_modules))])}
                RETURNING id;"""

    variables = [tuple(i.values()) for i in raw_modules]

    result = db.custom_call(
        cursor=cursor,  # type: ignore
        query=query,
        variables=variables,
        type_of_answer=db.ANSWER_TYPE.NO_ANSWER,
    )

    return result


@db.cursor_handling(manually_supply_cursor=False)
def remove_already_computed(modules):
    pass


@db.cursor_handling(manually_supply_cursor=False)
def handle_single_module(module: Any, module_text: str) -> Result:
    """
    handle everything for single module
    therefore extract data from module and save extracted data to database

    Args:
        module (Any): module dict with important raw data
        module_text (str): raw module text to extract data from

    Returns:
        Response[Any, Any]: response object containing either nothing or error information
    """
    try:
        result = emi(module_text=module_text)  # type: ignore
    except Exception as e:
        return Result(error=str(e), additional_information=module)
    # append extracted data to module dict
    module["extracted_data"] = result.model_dump()
    if module["extracted_data"]["title"] is None:
        module["extracted_data"]["title"] = module["module_code"]
    # save to results
    results.append(module)

    # save to database
    db_module = {
        key: Json(value)
        if isinstance(value, dict) or isinstance(value, list)
        else value
        for key, value in module["extracted_data"].items()
    }
    db_module["raw_module_id"] = module["id"]
    db_res = db.insert(
        cursor=cursor,  # type: ignore
        table="unia.modules_ai_extracted",
        values=db_module,
        returning_column="id",
    )
    # if error occurs, log module for later inspection
    if db_res.is_error:
        print(f"\n{db_res.error}")
        print(
            f"\nError saving module {module.get('module_code', 'unknown')} to database."
        )
        return Result(error=str(db_res.error), additional_information=module)

    return Result(data=module)


# @db.cursor_handling(manually_supply_cursor=False)
def extract_module_data(
    modules: list[dict[str, Any]], save_path: str | None = None, cursor=None
) -> list[dict[str, Any]]:
    """
    extract structured json data from raw module texts using ai

    Args:
        modules (list[dict[str, Any]]): list of raw module texts
        save_path (str | None): optional path to save the extracted module data as json file
                                if not specified, data won't be saved persistently
        cursor: database cursor, supplied automatically by decorator

    Returns:
        list[dict[str, Any]]: list of extracted module data
    """
    # initialize result and error lists
    results = []
    errors = []

    # for each module, extract data using ai
    for module in tqdm(modules):
        # extract data
        try:
            result = handle_single_module(module, module_text=module["content"])
            # NEWLY IGNORED
            # result = emi(module_text=module["content"])  # type: ignore
        except:
            continue
        # NEWLY ADDED
        if result.is_error:
            errors.append(result.additional_information)
            continue
        results.append(result.data)
        # NEWLY IGNORED
        """
        # append extracted data to module dict
        module["extracted_data"] = result.model_dump()
        # save to results
        results.append(module)

        # save to database
        db_module = {key: Json(value) if isinstance(value, dict) or isinstance(value, list) else value for key, value in module["extracted_data"].items()}
        db_res = db.insert(
            cursor=cursor, # type: ignore
            table="unia.modules_ai_extracted",
            values=db_module,
            returning_column="id"
        )
        # if error occurs, log module for later inspection
        if db_res.is_error:
            errors.append(module)
            print(f"\n{db_res.error}")
            print(f"\nError saving module {module.get('module_code', 'unknown')} to database.")
        """

    # save results to json files if path is provided
    if save_path is not None:
        with open(os.path.expanduser(save_path), "w", encoding="utf-8") as file:
            json.dump(results, file, indent=4)

    # save errors to json file for later inspection
    if errors:
        with open(
            os.path.expanduser("~/mhbai/_temp_extraction_errors.json"),
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(errors, file, indent=4)

    return results


if __name__ == "__main__":
    modules = load_pdf_modules(pdf_folder="~/mhbai/pdfs/", from_db=True)
    print()
    print("Extracting data from modules using AI...")
    results = extract_module_data(
        modules, save_path="~/mhbai/_temp_extracted_modules.json"
    )
