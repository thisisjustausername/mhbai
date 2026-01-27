import os
import multiprocessing
import math
from psycopg2.extras import Json
from psycopg2.extensions import cursor as Cursor
from typing import Any

from database import database as db
from ai.overall_ai.data_extraction import extract_module_info as emi
from datatypes.response import Response as FuncRes, Message, Status
from pdf_reader import pdf_reader_toc as prt
from datatypes.result import Result
from ai.overall_ai.full_extraction import extract_modules_from_files


def save_raw(cursor: Cursor, modules):
    query = f"""INSERT INTO unia.modules (title, module_code, content, goals, ects, pages, mhb_id)
               VALUES {", ".join(["%s" for _ in range(len(modules))])}
                RETURNING id;"""

    result = db.custom_call(
        cursor=cursor,  # type: ignore
        query=query,
        variables=modules,
        type_of_answer=db.ANSWER_TYPE.NO_ANSWER,
    )

    return result


@db.cursor_handling(manually_supply_cursor=False)
def load_pdf_modules(cursor: Cursor | None = None) -> FuncRes:
    """
    load all raw modules from all pdfs in a folder
    remove duplicates on the way in order to keep the ai data extraction time minimal

    Args:
        cursor: specified by decorator

    Returns:
        FuncRes: FuncRes object containing success or error
    """

    result = db.select(
        cursor=cursor,  # type: ignore
        type_of_answer=db.ANSWER_TYPE.LIST_ANSWER,
        table="unia.mhbs",
        keywords=["id", "folder", "pdf_name"],
    )

    if result.is_error:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="database error",
                info="Fetching mhbs from database failed",
                code=500,
            ),
            status=Status.FULL_ERROR,
        )

    # fetch all mhb pdfs from folder
    files = [
        (path, f["id"])
        for f in result.data
        if os.path.isfile(
            (
                path := os.path.expanduser(
                    os.path.join(f["folder"], str(f["id"]) + ".pdf")
                )
            )
        )
    ]

    # extract raw modules from each file
    print(f"Extracting raw module data from {len(files)} mhbs.")
    modules = []

    # with multiprocessing
    cpu_count = multiprocessing.cpu_count()
    urls_per_job = math.ceil(len(files) / cpu_count)

    with multiprocessing.Pool(processes=cpu_count) as pool:
        results = [
            pool.apply_async(
                extract_modules_from_files,
                args=([i[0] for i in files[i : i + urls_per_job]], True),
            )
            for i in range(0, len(files), urls_per_job)
        ]
        for result in results:
            data = result.get()
            modules += data
    modules = [
        tuple(
            i["data"][e] if e != "pages" else Json(i["data"][e])
            for e in ["title", "module_code", "content", "goals", "ects", "pages"]
        )
        + (i["file"].split("/")[-1].split(".pdf")[0],)
        for i in modules
    ]

    result = save_raw(cursor=cursor, modules=modules)  # type: ignore
    if result.is_error:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="database error",
                info="Inserting modules into database failed",
                code=500,
            ),
            status=Status.FULL_ERROR,
        )

    return FuncRes(status=Status.FULL_SUCCESS)


if __name__ == "__main__":
    load_pdf_modules()
