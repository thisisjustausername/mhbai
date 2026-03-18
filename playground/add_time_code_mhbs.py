import re
from pdf_reader.pdf_extractor import Pdf
from database import database as db
import os


cursor = db.connect()
mhbs = db.select(cursor=cursor, table="unia.mhbs", keywords=["folder", "id"])
if mhbs.is_error:
    raise UserWarning("Error occurred in db")

mhbs = mhbs.data
mhbs = [
    (i["id"], os.path.expanduser(i["folder"] + str(i["id"])) + ".pdf") for i in mhbs
]
for a in mhbs:
    time_code = None
    try:
        pdf = Pdf(pdf_path=a[1]).extract_objects()
        index_match = next(
            i.get("data", "")
            for i in pdf
            if re.search(
                r".*? Tm \[(.*?[WS][omint]{3}ersemester \d{4}.*?)\] .*?",
                i.get("data", ""),
            )
        )
        year_semester = re.search(
            r"[WS][omint]{3}ersemester \d{4}.*? ", index_match
        ).group(0)[:-1]
        time_code = int(
            year_semester.split(" ")[-1].split("/")[0].split(")]")[0]
            + str(0 if year_semester.startswith("S") else 1)
        )
    except Exception as e:
        print(f"Exception occurred: {e}")
        continue

    res = db.update(
        cursor=cursor,
        table="unia.mhbs",
        arguments={"version": time_code},
        conditions={"id": a[0]},
        returning_column="id",
    )

    if res.is_error:
        print(f"Error occurred during update: {res.error}")
    if res.data is None:
        print("Nothing returned from update")

    print(res.data)
