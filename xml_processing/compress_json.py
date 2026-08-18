"""
Compress the json schema and change it for RAG for AI
"""

# TODO: mapping for exams and parts doesn't fully work yet
#
import json
import os
import re
from pathlib import Path
from typing import Any

from xml_processing.find_information import recursive_walk


def compress_json(local_path: Path) -> dict[str, Any] | None:
    '''
    Compress the json schema and change it for RAG for AI

    Args:
        local_path (Path): The path to the JSON file to compress
    Returns:
        dict[str, Any] | None: the compressed and cleaned json or None when the file is malformed
    '''
    path = "uni-a_mhbs_json/"
    file_path = os.path.join(path, local_path)

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data is None:
        return None

    recursive_walk(data, remove_keys = [], rename_keys = {}, retype_values={}, replace_values = {"keine Angabe": None, 'NA': None})
    mhb = {}
    mhb["path"] = str(local_path)
    mhb["name"] = data.get("name", None)
    mhb["description"] = data.get("description", None)
    mhb["start_semester"] = data.get("start_semester", None)
    facs = data.get("mhb_pos_unclear-", {})
    if isinstance(facs, dict):
        facs = [facs]
    facs = [[f.get("mhb_po", {})] if isinstance(f.get("mhb_po", {}), dict) else f.get("mhb_po", {}) for f in facs]
    facs = [[e.get("po", {}).get("studfach", {}).get("fak", {}).get("zeugnisbez", None) for e in f] for f in facs]
    facs = {e for i in facs for e in i}
    mhb["faculties"] = list(facs)
    mhb["mhb_group"] = data.get("mhb_group_name", None)

    mhb["module_groups"] = []
    for i in data.get("module_groups", []):
        module_group = {}
        module_group["name_letter"] = i.get("name", None)
        module_group["min_ects"] = i.get("min_ects", None)
        module_group["max_ects"] = i.get("max_ects", None)
        module_group["modules"] = []
        for j in i.get("modules", []):
            module = {}
            module["name"] = j.get("name", None)
            module["module_code"] = j.get("module_code", None)
            module["ects"] = j.get("ects", None)
            module["mandatory"] = j.get("is_mandatory", None)
            module["weekly_hours"] = j.get("weekly_hours", None)
            module["workload_hours"] = j.get("workload_hours", None)
            module["prerequisites"] = j.get("prerequisites", None)
            module["success_requirements"] = j.get("success_requirements", None)
            semesters = [j.get("min_semester", None), j.get("max_semester", None)]
            module["recommended_semester_span"] = None if all(s is None for s in semesters) else {"start_semester": semesters[0], "end_semester": semesters[1]}
            module["description"] = j.get("description", None)
            module["duration_in_semesters"] = j.get("duration_in_semesters", None)
            module["content"] = None if (a := re.sub(r'\s+', ' ', (j.get("content", "") or "")).strip()) == "" else a
            module["lecturer"] = j.get("lecturer", None)
            module["module_part_combinations"] = j.get("module_part_combinations", None)
            module["exam_outline"] = j.get("exam", None)
            module["goals"] = None if (a := re.sub(r'\s+', ' ', (j.get("goals", "") or "")).strip()) == "" else a
            module["international"] = True if j.get("international", None) == 1 else False if j.get("international", None) == 0 else None
            module["prerequisite_language"] = j.get("prerequisite_language", None)
            langs = sorted({e for e in [e.get("language", None) for e in j.get("languages", [])] if e is not None})
            module["languages"] = langs if len(langs) > 0 else None
            start_sem = j.get("available_semesters", {}).get("start_semester", {}).get("name", None)
            end_sem = j.get("available_semesters", {}).get("end_semester", {}).get("name", None)
            module["available_semesters"] = {"start_semester": start_sem, "end_semester": end_sem, "frequency": j.get("frequency", [{}])[0].get("frequency_name", None)}
            module["keywords"] = j.get("keywords", None)
            usability = j.get("usability", [])
            if isinstance(usability, dict):
                usability = [usability]
            module["usability"] = [e.get("name", None) for e in usability if e.get("name", None) is not None]
            module["faculty_chair"] = [e.get("name", None) for e in j.get("organization_owner", []) if e.get("role", "").lower() == "owner" and e.get("name", None) is not None]

            module["workloads"] = [{
                "name": i.get("type", {}).get("name", None),
                "in_presence": True if (a := i.get("in_presence", None)) == 1 else False if a == 0 else None,
                "time_expenditure": i.get("workload_hours", None)} for i in (j.get("workloads", []) or [])]

            # TODO: join exams with parts over ids
            exams = []
            for e in j.get("exams", []):
                exam = {}
                exam["name"] = e.get("name", None)
                exam["duration"] = (str(e.get("duration", None)) + ((" " + e.get("time_unit", None)) if e.get("time_unit", None) is not None else "")) if e.get("duration", None) is not None else None
                exam["graded"] = e.get("graded", None)
                exam["portion_of_grade"] = e.get("portion_of_grade", None)
                exam["preparation"] = e.get("preparation", None)
                exam["deadline"] = e.get("deadline", None)
                exam["description"] = e.get("description", None)
                exam["type"] = e.get("type", None)
                langs = sorted({a for a in [a.get("language", None) for a in e.get("languages", [])] if a is not None})
                exam["languages"] = langs if len(langs) > 0 else None
                freq = e.get("exam_frequency", [{}])
                if isinstance(freq, dict):
                    freq = [freq]
                exam["exam_frequency"] = freq[0].get("name", None)
                exam["id"] = e.get("id", None)
                exams.append(exam)

            parts = []
            taken_exams = []
            for k in j.get("parts", []):
                part = {}
                exam_ids = [l.get('id', None) for l in (k.get("exams", []) or [])] # .get("modul_lv_prf", {}).get("modul_prf", None) # NOTE: replaced module_part_exams with exams
                exam_ids = [l for l in exam_ids if l is not None]
                temp_exams_mod_ids = [a['id'] for a in exams]
                free_exam_ids = [l for l in exam_ids if l not in temp_exams_mod_ids]
                part["exams"] = None if len(exam_ids) == 0 else [a for a in exams if a["id"] in exam_ids]
                if part["exams"] == []:
                    part["exams"] = None
                taken_exams.extend(list({[l["id"] for l in part["exams"] or []]}.intersection(set(temp_exams_mod_ids))))
                t_exams = []
                for l in [m for m in (k.get("exams", []) or []) if m.get("id", None) in free_exam_ids]:
                    exam = {}
                    exam["name"] = l.get("name", None)
                    exam["duration"] = str(l.get("duration", None)) + ((" " + l.get("time_unit", None)) if l.get("time_unit", None) is not None else "")
                    exam["graded"] = l.get("graded", None)
                    exam["portion_of_grade"] = l.get("portion_of_grade", None)
                    exam["preparation"] = l.get("preparation", None)
                    exam["deadline"] = l.get("deadline", None)
                    description = l.get("description", None)
                    exam["description"] = description if not isinstance(description, dict) else description.get('html', {}).get('body', None)
                    exam["type"] = l.get("type", None)
                    langs = sorted({a for a in [a.get("language", None) for a in l.get("languages", [])] if a is not None})
                    exam["languages"] = langs if len(langs) > 0 else None
                    freq = l.get("exam_frequency", [{}])
                    if isinstance(freq, dict):
                        freq = [freq]
                    exam["exam_frequency"] = freq[0].get("name", None)
                    exam["id"] = l.get("id", None)
                    t_exams.append(exam)

                if part["exams"] is not None:
                    part["exams"].append(t_exams if len(t_exams) > 0 else []) # type: ignore
                else:
                    part["exams"] = t_exams if len(t_exams) > 0 else None
                part["name"] = k.get("name", None)
                part["weekly_hours"] = k.get("weekly_hours", None)
                part["mandatory"] = k.get("mandatory", None)
                part["ects"] = k.get("ects", None)

                # remove unremoved xhtml with empty content
                content = k.get("content", "") if isinstance(k.get("content", ""), str) else ""

                part["content"] = None if (a := re.sub(r'\s+', ' ', (content).strip())) == "" else a
                part["literature"] = k.get("literature", None)
                part["frequency"] = k.get("frequency", [{}])[0].get("frequency_name", None)
                part["success_requirements"] = k.get("success_requirements", None)
                part["learning_methods"] = k.get("learning_methods", None)

                # remove unremoved xhtml with empty content
                goals = k.get("goals", "") if isinstance(k.get("goals", ""), str) else ""

                part["goals"] = None if (a := re.sub(r'\s+', ' ', (goals).strip())) == "" else a
                langs = sorted({a for a in [a.get("name", None) for a in k.get("languages", [])] if a is not None})
                part["languages"] = langs if len(langs) > 0 else None
                tms = [l.get("name", None) for l in (k.get("teaching_methods", []) or []) if l is not None]
                tms = [l for l in tms if l is not None]
                part["teaching_methods"] = tms if len(tms) > 0 else None
                part["lecturer"] = k.get("lecturer", module["lecturer"]) # TODO check whether that is good
                part["workloads"] = k.get("workloads", None)
                part["subsubparts"] = [{
                    "name": l.get("name", None),
                    "type": l.get("type", None),
                    "semester": l.get("semester_name", None),
                    "delivery_form": l.get("delivery_form", None),
                    "ects": l.get("ects", None),
                    "content": None if (a := re.sub(r'\s+', ' ', (l.get("content", "") or "").strip())) == "" else a} for l in k.get("subparts", [])]
                parts.append(part)

            module["parts"] = parts
            exams = [e for e in exams if e["id"] not in taken_exams]
            module["exams"] = exams

            module_group["modules"].append(module)
        mhb["module_groups"].append(module_group)

    return mhb


def json_to_compressed_json(json_path: Path | tuple[Path, int]) -> tuple[dict[str, Any] | None, Path | tuple[Path, int]]:
    """
    Finished pipeline step, that combines all of the steps above.
    Convert json to a compressed format

    Args:
        xml_path (Path | tuple[Path, int]): The path to the XML file to convert
    Returns:
        tuple(dict[str, Any] | None, Path | tuple[Path, int]): the converted and cleaned json and the path to the XML file
    """
    if isinstance(json_path, tuple):
        json_path, index = json_path
    data = compress_json(json_path)
    if data is None:
        print(f"Malformed JSON file: {json_path}")
    return data, (json_path, index)

if __name__ == "__main__":
    local_path = "BachelorStudiengaenge/Bachelor of Arts (Haupt und Nebenfach)/Anglistik  Amerikanistik (Hauptfach)/POVersion 2023/Sommersemester 2024/Bachelor_of_Arts_Anglistik_Amerikanistik_Hauptfach_BaPO_2023_ID44938_1_de_20240304_0739.json"
    mhb = compress_json(Path(local_path))
    print(json.dumps(mhb, indent=2, ensure_ascii=False))
