from io import BytesIO
import hashlib
from psycopg2.extensions import cursor as Cursor
from pdf_reader import pdf_reader_toc as prt
from database import database as db
from datatypes.response import Response as FuncRes, Message, Status


def get_raw_module_matching(cursor: Cursor, file: BytesIO) -> FuncRes:
    """
    Fetches raw module data from a PDF file and matches it with entries in the database.

    This function parses the provided PDF file to extract raw module texts, hashes their content
    for efficient lookup, removes duplicates, and queries the database for matching modules
    based on the content hash. It returns a FuncRes object indicating the result of the operation.

    Args:
        cursor (Cursor): Database cursor used for executing queries.
        file (BytesIO): PDF file containing module data.

    Returns:
        FuncRes: Result object containing matched module data or error information.
    """
    modules: prt.Modules = prt.Modules(pdf_file=file)  # type: ignore
    raw_modules = modules.raw_module_texts()

    # hash content in order to query the database faster
    hashed_contents = [
        hashlib.md5(raw_module["content"]).hexdigest() for raw_module in raw_modules
    ]

    # in order to reduce processing time with the ai, remove duplicates
    hashed_contents = list(set(hashed_contents))

    # works without module code since content is already unique
    result = db.select(
        cursor=cursor,  # type: ignore
        table="unia.modules_raw",
        type_of_answer=db.ANSWER_TYPE.LIST_ANSWER,
        keywords=["id, module_code, content, content_md5"],
        specific_where=f"content_md5 IN ({', '.join('%s' for i in range(len(hashed_contents)))})",
        variables=hashed_contents,
    )

    if result.is_error:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Fetching modules from db failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )

    if len(result.data) != len(hashed_contents):
        return FuncRes(
            success_data=result.data,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Not all modules found",
                details={
                    "error": "Not all modules found",
                    "missing_modules": NotImplementedError(
                        "Missing modules mentioned by module_id not implemented yet"
                    ),
                },
                code=500,
            ),
            status=Status.PARTIAL_SUCCESS,
        )

    # matched data important to show pages, do it differently though
    # NOTE: since content contains module_code, it is unique for different module codes
    # matched_data =

    return FuncRes(
        success_data=result.data,
        message=Message(
            name="Module ids fetched",
            type="success",
            category="matching preparation",
            info="Fetched module ids for matching with ai data",
        ),
        status=Status.FULL_SUCCESS,
    )


@db.cursor_handling(manually_supply_cursor=False)
def get_mhb_modules(file: BytesIO, cursor: Cursor | None) -> FuncRes:
    pass
