"""
Compress the json schema and change it for RAG for AI
"""

# TODO: mapping for exams and courses doesn't fully work yet
#
import json
import os
from pathlib import Path
from typing import Any
import re


def compress_json(local_path: Path):
    path = "uni-a_mhbs_json/"
    file_path = os.path.join(path, local_path)

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if data is None:
        print(f"Error: No data found in {file_path}")
        return None

    mhb = dict()
    mhb["path"] = str(local_path)
    mhb["name"] = data.get("name", None)
    mhb["description"] = data.get("description", None)
    mhb["start_semester"] = data.get("start_semester", None)
    facs = data.get("mhb_pos_unclear-", dict())
    if isinstance(facs, dict):
        facs = [facs]
    facs = [[f.get("mhb_po", dict())] if isinstance(f.get("mhb_po", dict()), dict) else f.get("mhb_po", dict()) for f in facs]
    facs = [[e.get("po", dict()).get("studfach", dict()).get("fak", dict()).get("zeugnisbez", None) for e in f] for f in facs]
    facs = set([e for i in facs for e in i])
    mhb["faculties"] = list(facs)
    mhb["mhb_group"] = data.get("mhb_group_name", None)

    mhb["module_groups"] = []
    for i in data.get("module_groups", []):
        module_group = dict()
        module_group["name_letter"] = i.get("name", None)
        module_group["min_ects"] = i.get("min_ects", None)
        module_group["max_ects"] = i.get("max_ects", None)
        module_group["modules"] = []
        for j in i.get("modules", []):
            module = dict()
            module["name"] = j.get("name", None)
            module["module_code"] = j.get("module_code", None)
            module["ects"] = j.get("ects", None)
            module["mandatory"] = j.get("is_mandatory", None)
            module["weekly_hours"] = j.get("weekly_hours", None)
            module["workload_hours"] = j.get("workload_hours", None)
            module["prerequisites"] = j.get("prerequisites", None)
            module["success_requirements"] = j.get("success_requirements", None)
            module["frequency"] = j.get("frequency", [dict()])[0].get("frequency_name", None)
            semesters = [j.get("min_semester", None), j.get("max_semester", None)]
            module["recommended_semester"] = None if all(s is None for s in semesters) else f"{semesters[0] if semesters[0] is not None else 'NA'} - {semesters[1] if semesters[1] is not None else 'NA'}"
            module["description"] = j.get("description", None)
            module["duration_in_semesters"] = j.get("duration_in_semesters", None)
            module["content"] = None if (a := re.sub(r'\s+', ' ', (j.get("content", "") or "")).strip()) == "" else a
            module["lecturer"] = j.get("lecturer", None)
            module["module_course_combinations"] = j.get("module_course_combinations", None)
            module["exam_outline"] = j.get("exam", None)
            module["goals"] = None if (a := re.sub(r'\s+', ' ', (j.get("goals", "") or "")).strip()) == "" else a
            module["international"] = True if j.get("international", None) == 1 else False if j.get("international", None) == 0 else None
            module["prerequisite_language"] = j.get("prerequisite_language", None)
            langs = set(e for e in [e.get("language", None) for e in j.get("languages", [])] if e is not None)
            module["languages"] = ", ".join(langs) if len(langs) > 0 else None
            start_sem = j.get("available_semesters", dict()).get("start_semester", dict()).get("name", "NA")
            end_sem = j.get("available_semesters", dict()).get("end_semester", dict()).get("name", "NA")
            module["available_semesters"] = f"{start_sem} - {end_sem}"
            module["keywords"] = j.get("keywords", None)
            usability = j.get("usability", [])
            if isinstance(usability, dict):
                usability = [usability]
            module["usability"] = [e.get("name", None) for e in usability if e.get("name", None) is not None]
            module["faculty_chair"] = [e.get("name", None) for e in j.get("organization_owner", []) if e.get("role", "").lower() == "owner" and e.get("name", None) is not None]

            module["workloads"] = [{
                "name": i.get("type", dict()).get("name", None),
                "in_presence": True if (a := i.get("in_presence", None)) == 1 else False if a == 0 else None,
                "time_expenditure": i.get("workload_hours", None)} for i in (j.get("workloads", []) or [])]

            # TODO: join exams with courses over ids
            exams = []
            for e in j.get("exams", []):
                exam = dict()
                exam["name"] = e.get("name", None)
                exam["duration"] = str(e.get("duration", None)) + ((" " + e.get("time_unit", None)) if e.get("time_unit", None) is not None else "")
                exam["graded"] = e.get("graded", None)
                exam["portion_of_grade"] = e.get("portion_of_grade", None) if e.get("portion_of_grade", None) is not None else "NA"
                exam["preparation"] = e.get("preparation", None)
                exam["deadline"] = e.get("deadline", None)
                exam["description"] = e.get("description", None)
                exam["type"] = e.get("type", None)
                langs = set(a for a in [a.get("language", None) for a in e.get("languages", [])] if a is not None)
                exam["languages"] = ", ".join(langs) if len(langs) > 0 else None
                freq = e.get("exam_frequency", [dict()])
                if isinstance(freq, dict):
                    freq = [freq]
                exam["exam_frequency"] = freq[0].get("name", None)
                exam["id"] = e.get("id", None)
                exams.append(exam)

            courses = []
            taken_exams = []
            for k in j.get("courses", []):
                course = dict()
                exam_ids = [l.get('id', None) for l in (k.get("exams", list()) or [])] # .get("modul_lv_prf", dict()).get("modul_prf", None) # NOTE: replaced module_course_exams with exams
                exam_ids = [l for l in exam_ids if l is not None]
                temp_exams_mod_ids = [a['id'] for a in exams]
                free_exam_ids = [l for l in exam_ids if l not in temp_exams_mod_ids]
                course["exams"] = None if len(exam_ids) == 0 else [a for a in exams if a["id"] in exam_ids]
                if course["exams"] == []:
                    course["exams"] = None
                taken_exams.extend(list(set([l["id"] for l in course["exams"] or []]).intersection(set(temp_exams_mod_ids))))
                t_exams = []
                for l in [m for m in (k.get("exams", []) or []) if m.get("id", None) in free_exam_ids]:
                    exam = dict()
                    exam["name"] = l.get("name", None)
                    exam["duration"] = str(l.get("duration", None)) + ((" " + l.get("time_unit", None)) if l.get("time_unit", None) is not None else "")
                    exam["graded"] = l.get("graded", None)
                    exam["portion_of_grade"] = l.get("portion_of_grade", None) if l.get("portion_of_grade", None) is not None else "NA"
                    exam["preparation"] = l.get("preparation", None)
                    exam["deadline"] = l.get("deadline", None)
                    exam["description"] = l.get("description", None)
                    exam["type"] = l.get("type", None)
                    langs = set(a for a in [a.get("language", None) for a in l.get("languages", [])] if a is not None)
                    exam["languages"] = ", ".join(langs) if len(langs) > 0 else None
                    freq = l.get("exam_frequency", [dict()])
                    if isinstance(freq, dict):
                        freq = [freq]
                    exam["exam_frequency"] = freq[0].get("name", None)
                    exam["id"] = l.get("id", None)
                    t_exams.append(exam)

                if course["exams"] is not None:
                    course["exams"].append(t_exams if len(t_exams) > 0 else []) # type: ignore
                else:
                    course["exams"] = t_exams if len(t_exams) > 0 else None
                course["name"] = k.get("name", None)
                course["weekly_hours"] = k.get("weekly_hours", None)
                course["mandatory"] = k.get("mandatory", None)
                course["ects"] = k.get("ects", None)

                # remove unremoved xhtml with empty content
                content = k.get("content", "") if isinstance(k.get("content", ""), str) else ""

                course["content"] = None if (a := re.sub(r'\s+', ' ', (content).strip())) == "" else a
                course["literature"] = k.get("literature", None)
                course["frequency"] = k.get("frequency", [dict()])[0].get("frequency_name", None)
                course["success_requirements"] = k.get("success_requirements", None)
                course["learning_methods"] = k.get("learning_methods", None)

                # remove unremoved xhtml with empty content
                goals = k.get("goals", "") if isinstance(k.get("goals", ""), str) else ""

                course["goals"] = None if (a := re.sub(r'\s+', ' ', (goals).strip())) == "" else a
                langs = set(a for a in [a.get("name", None) for a in k.get("languages", [])] if a is not None)
                course["languages"] = ", ".join(langs) if len(langs) > 0 else None
                tms = [l.get("name", None) for l in (k.get("teaching_methods", []) or []) if l is not None]
                tms = [l for l in tms if l is not None]
                course["teaching_methods"] = ", ".join(tms) if len(tms) > 0 else None
                course["lecturer"] = k.get("lecturer", module["lecturer"]) # TODO check whether that is good
                course["workloads"] = k.get("workloads", None)
                course["subparts"] = [{
                    "name": l.get("name", None),
                    "type": l.get("type", None),
                    "semester": l.get("semester_name", None),
                    "delivery_form": l.get("delivery_form", None),
                    "ects": l.get("ects", None),
                    "content": None if (a := re.sub(r'\s+', ' ', (l.get("content", "") or "").strip())) == "" else a} for l in k.get("subcourses", [])]
                courses.append(course)

            module["courses"] = courses
            exams = [e for e in exams if e["id"] not in taken_exams]
            module["exams"] = exams

            module_group["modules"].append(module)
        mhb["module_groups"].append(module_group)
    return mhb


def json_to_compressed_json(json_path: Path) -> tuple[dict[str, Any], Path]:
    """
    Finished pipeline step, that combines all of the steps above.
    Convert json to a compressed format

    Args:
        xml_path (Path): The path to the XML file to convert
    Returns:
        tuple(dict[str, Any], Path): the converted and cleaned json and the path to the XML file
    """
    data = compress_json(json_path)

    return data, json_path

if __name__ == "__main__":
    local_path = "BachelorStudiengaenge/Bachelor of Arts (Haupt und Nebenfach)/Anglistik  Amerikanistik (Hauptfach)/POVersion 2023/Sommersemester 2024/Bachelor_of_Arts_Anglistik_Amerikanistik_Hauptfach_BaPO_2023_ID44938_1_de_20240304_0739.json"
    mhb = compress_json(Path(local_path))
    print(json.dumps(mhb, indent=2, ensure_ascii=False))
