"""
reconstruct the mapping from the original data to the computed data since I somehow under mysterious
circumstances did not save the mapping.
"""

import json

from database import database as db
from ai.overall_ai.full_extraction import load_pdf_modules


@db.cursor_handling(manually_supply_cursor=False)
def read_data(cursor=None):
    """
    Fetch the raw and the computed data from the database

    Returns:

    """
    result = db.select(
        cursor=cursor,  # type: ignore
        table="unia.modules_ai_extracted",
        keywords=["id", "title", "module_code", "ects", "lecturer", "contents", "goals", "requirements", "expense", 
                  "success_requirements", "weekly_hours", "recommended_semester", "exams", "module_parts"],
        answer_type=db.ANSWER_TYPE.LIST_ANSWER,
    )
    if result.is_error:
        raise Exception("Error occurred reading the computed data")

    computed_data = result.data

    result = load_pdf_modules(pdf_folder="~/mhbai/pdfs/")

    raw_data = result

    return {"raw_data": raw_data, "computed_data": computed_data}


def compare_data(raw_data, computed_data, expected_matches: int):
    """
    Maps the raw data to the computed data and checks, whether the mapping is corrrect.
    
    Args:
        raw_data: list of raw data dicts
        computed_data: list of computed data dicts
        expected_matches: number of expected matches between raw and computed data
        mp_job_size: the multiprocessing job size used during extraction
    
    Returns:
        dict: mapping from raw data index to computed data index
    """
    for index, i in enumerate(computed_data):
        test = [
                    e for e in raw_data
                    if i["module_code"] == e["module_code"]
                    and (i["lecturer"] is None or all(a in e["content"] for a in i["lecturer"].split(", ")))
                    and (i["ects"] is None or str(i["ects"]) in e["content"])
                    ]
        if index == 44:
            print(json.dumps(i, indent=4))
            print(f"Found: {[e for e in raw_data if i["module_code"] == e["module_code"]]}")
        print(index, len(test))
    matched = [{"computed": i, 
                "raw_matches": [
                    e for e in raw_data
                    if i["module_code"] == e["module_code"]
                    and (i["lecturer"] is None or i["lecturer"] in e["content"])
                    and (i["ects"] is None or str(i["ects"]) in e["content"])
                    ]} for i in computed_data]

if __name__ == "__main__":
    result = read_data()
    result = compare_data(result["raw_data"], result["computed_data"], expected_matches=37517)
