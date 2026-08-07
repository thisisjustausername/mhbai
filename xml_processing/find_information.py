"""
Convert raw Studis XML-files for study programs (courses) to a new JSON schema
"""

import json
from typing import Callable


def recursive_walk(
            d: dict | list,
            remove_keys: list[str],
            rename_keys: dict[str, str],
            retype_values: dict[str, Callable],
            replace_values: dict[int | str | None, int | str | None]) -> list | None:
        """
        recursively walk through a dictionary and remove or rename keys and retype or replace values

        Args:
            d (dict | list): the dictionary or list to walk through
            remove_keys (list[str]): the keys to remove
            rename_keys (dict[str, str]): the keys to rename, with the new name as value
            retype_values (dict[str, Callable]): the keys to retype, with the new type as value
            replace_values (dict[int | str | float | None, int | str | float | None]): the values to replace, with the new value as value

        Returns:
            None | list: changes happen inplace, except for lists
        """
        if isinstance(d, list):
            new_list = []
            for i in d:
                if str(type(i)) in retype_values:
                    try:
                        i = retype_values[str(type(i))](i)
                    except ValueError:
                        pass
                    new_list.append(i)
                elif (i is None or isinstance(i, (int, str, float))) and i in replace_values:
                    i = replace_values[i]
                    new_list.append(i)
                elif isinstance(i, dict):
                    recursive_walk(i, remove_keys, rename_keys, retype_values, replace_values)
                    new_list.append(i)
                elif isinstance(i, list):
                    i = recursive_walk(i, remove_keys, rename_keys, retype_values, replace_values)
                    new_list.append(i)
                else:
                    new_list.append(i)
            return new_list

        keys = list(d.keys())
        for key in keys:
            # remove key if it is in the remove_keys list
            if key in remove_keys:
                d.pop(key)
                continue

            # recursively walk through the dictionary if the value is a dictionary or a list
            if isinstance(d[key], dict):
                recursive_walk(d[key], remove_keys, rename_keys, retype_values, replace_values)
            elif isinstance(d[key], list):
                d[key] = recursive_walk(d[key], remove_keys, rename_keys, retype_values, replace_values)
            else:
                if str(type(d[key])) in retype_values:
                    try:
                        d[key] = retype_values[str(type(d[key]))](d[key])
                    except ValueError:
                        pass
                elif (d[key] is None or isinstance(d[key], (int, str, float))) and d[key] in replace_values:
                    d[key] = replace_values[d[key]]
                elif isinstance(d[key], dict):
                    recursive_walk(d[key], remove_keys, rename_keys, retype_values, replace_values)
                elif isinstance(d[key], list):
                    d[key] = recursive_walk(d[key], remove_keys, rename_keys, retype_values, replace_values)

            # rename key if it is in the rename_keys dictionary
            if key in rename_keys:
                d[rename_keys[key]] = d.pop(key)


def clean_mhb(data: dict) -> dict | None:
    """
    clean the mhb data by removing unnecessary keys and renaming keys

    Args:
        data (dict): the mhb data to clean
    Returns:
        dict | None: the cleaned mhb data; None if too much data is missing
    """

    mhb = data["modulhandbuch"]["modulhandbuch"]

    """
    # rename modulhandbuch to mhb_id
    mhb["mhb_id"] = mhb.pop("modulhandbuch")

    # rename bez to name
    mhb["name"] = mhb.pop("bez")

    # rename beschreibung to description
    mhb["description"] = mhb.pop("beschreibung")

    # rename sprache_beschreibung to language_description
    mhb["language_description"] = mhb.pop("sprache_beschreibung")

    # delete exportstatus
    mhb.pop("exportstatus")"""

    rename_keys = {
        "modulhandbuch": "mhb_id",
        "bez": "name",
        "beschreibung": "description",
    }

    remove_keys = [
        "sprache_beschreibung",
        "exportstatus",
        "kein_txtexport",
        "kein_export",
        "kurz",
        "modulstatus",
        "modulgruppehier",
        "nach_gruppen",
        "bezeichner",
        "modulstatus",
        "vla_orgnummer",
        "fremd",
        "sorted_alle_vor_module",
        "orga_zentral",
        "sos_fach_bez",
        "version_gruppe",
        "version_handbuch",
        "version"
    ]

    retype_values = {str(str): lambda x: int(x)}

    replace_values = {-1: None}

    d = mhb["mhb_pos"]
    if mhb["handbuch_gruppen"] is None:
        return None

    recursive_walk(mhb["handbuch_gruppen"]["handbuch_gruppe"], remove_keys, rename_keys, retype_values=retype_values, replace_values=replace_values)

    # print(json.dumps(mhb, indent=4)[:10000])
    # print(mhb["handbuch_gruppen"]["handbuch_gruppe"][0]["modulgruppe"]["gruppe_module"]["gruppe_modul"][0]["studien_modul"].keys())

    new_mhb = {}
    new_mhb["id"] = mhb.get("modulhandbuch", None)
    new_mhb["name"] = mhb.get("bez", None)
    new_mhb["description"] = m.split(" (")[0] if (m := mhb.get("beschreibung", None)) else None
    new_mhb["language_description"] = m.split(" (")[0] if ( m:= mhb.get("sprache_beschreibung", None)) else None
    new_mhb["start_semester"] = mhb.get("semester", [{}])[0].get("zeugnisbez", None)
    new_mhb["mhb_pos_unclear-"] = mhb.get("mhb_pos", None)
    new_mhb["mhb_group_id"] = mhb.get("orgeinheit", {}).get("orgeinheit", None)
    new_mhb["mhb_group_name"] = mhb.get("orgeinheit", {}).get("bez", None)
    new_mhb["module_groups"] = []

    new_module_groups = []

    language_mappings = {"sprache": "langugage_id", "name": "language"}

    for i in mhb.get("handbuch_gruppen", {}).get("handbuch_gruppe", []):
        if isinstance(i, str):
            continue
        new_module_group = {}
        new_module_group["order"] = i.get("reihenfolge", None)
        new_module_group["id"] = i.get("modulgruppe", {}).get("modulgruppe", None)
        new_module_group["min_ects"] = i.get("modulgruppe", {}).get("ectsmin", None)
        new_module_group["max_ects"] = i.get("modulgruppe", {}).get("ectsmax", None)
        new_module_group["po_version_unclear-"]= i.get("modulgruppe", {}).get("bezeichnung", None)
        new_module_group["name_letter"] = i.get("modulgruppe", {}).get("name", [None])[0]
        new_module_group["type"] = i.get("modulgruppe", {}).get("name", [None])[0][2:].split(" (")[0]
        new_module_group["name"] = i.get("modulgruppe", {}).get("name", [None])[0].split("): ")[-1]

        if isinstance((i.get("modulgruppe", {}).get("gruppe_module", {}) or {}).get("gruppe_modul", None), dict):
            i["modulgruppe"]["gruppe_module"]["gruppe_modul"] = [i.get("modulgruppe", {}).get("gruppe_module", {}).get("gruppe_modul", None)]

        modules = []
        for e in (i.get("modulgruppe", {}).get("gruppe_module", {}) or {}).get("gruppe_modul", []):
            module = {}
            # important: studien_modul, ordnummer, pflicht, fachsem, gruppe_modul_art
            module["order"] = e.get("ordnummer", None)
            module["is_mandatory"] = a if (a := e.get("pflicht", None)) is not None and a != -1 else None if (b := e.get("gruppe_modul_art", {}).get("gruppe_modul_art", -1)) == -1 else b == 1
            module["semester"] = e.get("fachsem", None)

            mod = e.get("studien_modul", None)

            # TODO: check keys: ects_info, url, haeufigkeit, ects_schluessel, bemerkung_extern, bemerkung_intern, nutzer, nachhaltigkeit, sprache_nachhaltigkeit, drucken, nur_eng_drucken, sprache_haeufigkeit, modul_prfs.modulprf.schl_komp

            module["id"] = mod.get("studien_modul", None)
            module["created_at"] = mod.get("zeitstempel", None)
            module["module_code"] = mod.get("kurz_bez", None)
            module["ects"] = mod.get("ects_punkte", None)
            module["duration_in_semesters"] = mod.get("dauer", None)
            module["weekly_hours"] = a if (a := mod.get("sws", None)) is None or isinstance(a, int) else int(float(a.replace(",", ".")))
            module["min_semester"] = mod.get("minfachsem", None)
            module["max_semester"] = mod.get("maxfachsem", None)
            module["title"] = mod.get("sprache_bez", None)
            module["content"] = a if (a := mod.get("inhalte", None)) is None or not isinstance(a, str) else a.strip()
            module["workload_hours"] = a if (a := mod.get("arbeitsaufwand", None)) is None or isinstance(a, int) else int(float(a.replace(",", ".")))
            module["prerequisites"] = mod.get("voraussetzungen", None) # usually requirements
            module["success_requirements"] = mod.get("ects_bedingungen", None)
            module["frequency"] = [{"frequency_id": c.get("haeufigkeit", None), "frequency_name": c.get("name", None)} for c in mod.get("haeufigkeit", []) if isinstance(c, dict)]
            module["capacity"] = mod.get("kapazitaet", None)
            module["retake"] = mod.get("wiederholung", None)
            module["external_notes"] = mod.get("bemerkung_extern", None)
            module["internal_notes"] = mod.get("bemerkung_intern", None)
            module["lecturer"] = mod.get("nochzustaendig", None)
            module["mandatory_proof"] = mod.get("pflichtnachweis", None)
            module["creator"] = mod.get("nutzer", None)
            module["module_part_combination"] = mod.get("modullv_kombi", None)
            module["exam"] = mod.get("modulprf_kombi", None)
            module["goals"] = mod.get("lernziele", None)
            # module["graded"] = mod["unbenoted"] is False if mod["unbenoted"] is not None else # TODO: finish this with module_lvs
            module["international"] = mod.get("international", None)
            module["prerequisite_language"] = mod.get("sprache_voraussetzungen", None)
            module["notes_about_changes"] = mod.get("bem_aenderung", None)
            module["name"] = mod.get("name", None)
            # TODO: check removing duplicates from languages like below
            module["languages"] = [{language_mappings[k]: v for k, v in c.items() if k in ["sprache", "name"]} for c in mod.get("sprache", [])]

            persons = mod.get("person", [])

            module["maintainers"] = [{"person_id": c.get("personid", None), "role": c.get("role", None), "email": c.get("email", None), "first_name": c.get("vorname", None), "last_name": c.get("nachname", None), "degree": c.get("akadgrad", None)} for c in persons if c.get("personid", None) is not None and c.get("personid", 0) > 0]

            sem = mod.get("semester", [])
            start_semester = next((c for c in sem if c.get("role", "").lower() == "semesterbyvon"), None)
            start_semester = {"id": start_semester.get("semesternr", None), "name": start_semester.get("zeugnisbez", None), "short_name": start_semester.get("semester", None)} if start_semester else None
            end_semester = next((c for c in sem if c.get("role", "").lower() == "semesterbybis"), None)
            end_semester = {"id": end_semester.get("semesternr", None), "name": end_semester.get("zeugnisbez", None), "short_name": end_semester.get("semester", None)} if end_semester else None
            if end_semester and end_semester["id"] == -1 and end_semester["name"] is None and end_semester["short_name"] == "(leer)":
                end_semester["short_name"] = "unbegrenzt"
            sem_ids = [c.get("id", None) for c in [start_semester, end_semester] if c is not None]
            module["available_semesters"] = {"start_semester": start_semester,
                                            "end_semester": end_semester,
                                            "other_semesters": [{ "id": c.get("semesternr", None), "name": c.get("zeugnisbez", None), "short_name": c.get("semester", None)} for c in sem if c.get("semesternr", None) not in sem_ids]}

            module["keywords"] = mod.get("sorted_modul_stichworte", [])
            module["usability"] = {k: v for k, v in mod.get("verwendbarkeit", {}).items() if k != "sprache_bez"}
            module["organization_owner"] = [ {"organization_id": c.get("orgeinheit", None), "role": c.get("role", None), "name": c.get("name", None)} for c in mod.get("orgeinheit", [])]

            # print(list(mod.keys()))
            # TODO: check, whether it contains useful information
            mod_parts = (mod.get("modul_lvs", {}) or {}).get("modul_lv", [])
            # print(json.dumps(mod_parts, indent=4))

            # TODO: maybe add to lv if more exist, but probably not
            # TODO: look at modul_lv_prfs key
            # NOTE: ignore as that is a less precisely played duplicate of exam in parts (lv)
            exams = []
            ex = (mod.get("modul_prfs", {}) or {}).get("modul_prf", [])
            if not isinstance(ex, list):
                ex = [ex]
            for exa in ex:
                exam = {}
                exam["id"] = exa.get("modul_prf", None)
                exam["created_at"] = exa.get("zeitstempel", None)
                exam["duration"] = exa.get("pruefdauer", None)
                exam["graded"] = True if exa.get("unbenotet", None) == 0 else False if exa.get("unbenotet", None) == 1 else None
                exam["portion_of_grade"] = exa.get("anteil_note", None)
                exam["preparation"] = exa.get("vorbereitung", None)
                exam["lecture_duration"] = exa.get("vorlesung_dauer", None)
                exam["deadline"] = exa.get("frist", None)
                exam["name"] = exa.get("name", None)
                exam["description"] = exa.get("description", None)
                exam["type"] = exa.get("tptyp", {}).get("name", None)
                exam["type_id"] = exa.get("tptyp", {}).get("tptyp", None)
                exam["time_unit"] = (exa.get("zeiteinheit", [{}]) if isinstance(exa.get("zeiteinheit", [{}]), list) else [exa.get("zeiteinheit", [{}])])[0].get("name", None)
                exam["duration_type"] = exa.get("typ", None) # e.g. Vorbereituungszeit, ...
                exam["exam_organization"] = {"organization_id": exa.get("orgeinheit", {}).get("orgeinheit", None), "role": exa.get("orgeinheit", {}).get("role", None), "name": exa.get("orgeinheit", {}).get("name", None)}

                exam_langs = {}
                for c in exa.get("sprache", []):
                    if isinstance(c, str):
                        continue
                    if c.get("sprache", None) not in exam_langs:
                        exam_langs[c.get("sprache", None)] = {"language_id": c.get("sprache", None), "name": c.get("name", None)}
                exam["languages"] = [c for c in exam_langs.values()]

                exam["exam_frequency"] = {"frequency_id": exa.get("prfhaeufigkeit", {}).get("prfhaeufigkeit", None), "name": exa.get("prfhaeufigkeit", {}).get("name", None)}
                exam["module_part_exams"] = exa.get("modul_lv_prfs", [])
                exams.append(exam)
            module["exams"] = exams

            workloads = []
            if mod.get("workloads") is None:
                workloads = None
            else:
                for c in mod.get("workloads", {}).get("arbeitsaufwand", []):
                    if isinstance(c, str):
                        continue
                    workload = {}
                    workload["in_presence"] = c.get("praesenz", None)
                    workload["type"] = {"type_id": c.get("aufwand_art", {}).get("aufwand_art", None), "name": c.get("aufwand_art", {}).get("name", None)}
                    workload["workload_hours"] = a if (a := c.get("arbeitsaufwand", None)) is None or isinstance(a, int) else int(float(a.replace(",", ".")))

                    workloads.append(workload)

            module["workloads"] = workloads

            parts = []
            crss = (mod.get("modul_lvs", {}) or {}).get("modul_lv", [])
            if isinstance(crss, dict):
                crss = [crss]
            for c in crss:
                crs = {}
                crs["id"] = c.get("modul_lv", None)
                crs["created_at"] = c.get("zeitstempel", None)
                crs["weekly_hours"] = a if (a := c.get("sws", None)) is None or isinstance(a, int) else int(float(a.replace(",", ".")))
                crs["order"] = c.get("reihenfolge", None)
                crs["mandatory"] = True if c.get("pflicht", None) == 1 else False if c.get("pflicht", None) == 0 else None
                crs["ects"] = c.get("ects", None)
                crs["content"] = a if (a := c.get("inhalte", None)) is None or not isinstance(a, str) else a.strip()
                crs["literature"] = a if (a := c.get("literatur", None)) is None or not isinstance(a, str) else a.strip()
                crs["frequencies"] = [{"frequency_id": d.get("haeufigkeit", None), "frequency_name": d.get("name", None)} for d in mod.get("haeufigkeit", []) if isinstance(d, dict)]
                crs["workload_hours"] = a if (a := c.get("arbeitsaufwand", None)) is None or isinstance(a, int) else int(float(a.replace(",", ".")))
                crs["success_requirements"] = c.get("ects_bedingungen", None)
                crs["learning_methods"] = c.get("lernmethoden", None)
                crs["goals"] = c.get("lernziele", None)
                crs["name"] = c.get("name", None)
                crs_langs = {}
                for d in c.get("sprache", []):
                    if d.get("sprache", None) not in crs_langs:
                        crs_langs[d.get("sprache", None)] = {"language_id": d.get("sprache", None), "name": d.get("name", None)}
                crs["languages"] = list(crs_langs.values())
                crs["teaching_methods"] = None if c.get("lehrformen", None) is None else [{"id": d.get("modul_lv_form", None), "name": d.get("lehrformen", {}).get("modul_lv_form", {}).get("name", None)} for d in (c.get("lehrformen", {}).get("modul_lv_form", []) if isinstance(c.get("lehrformen", {}).get("modul_lv_form", []), list) else [c.get("lehrformen", {}).get("modul_lv_form", [])])]

                exam = {}
                if c.get("modul_prfs", None) is not None:
                    exams = []
                    ex = c.get("modul_prfs", {}).get("modul_prf", {})
                    if not isinstance(ex, list):
                        ex = [ex]
                    for exa in ex:
                        exam["id"] = exa.get("modul_prf", None)
                        exam["created_at"] = exa.get("zeitstempel", None)
                        exam["duration"] = exa.get("pruefdauer", None)
                        exam["graded"] = True if exa.get("unbenotet", None) == 0 else False if exa.get("unbenotet", None) == 1 else None
                        exam["portion_of_grade"] = exa.get("anteil_note", None)
                        exam["preparation"] = exa.get("vorbereitung", None)
                        exam["lecture_duration"] = exa.get("vorlesung_dauer", None)
                        exam["deadline"] = exa.get("frist", None)
                        exam["name"] = exa.get("name", None)
                        exam["description"] = exa.get("description", None)
                        exam["type"] = exa.get("tptyp", {}).get("name", None)
                        exam["type_id"] = exa.get("tptyp", {}).get("tptyp", None)
                        exam["time_unit"] = exa.get("zeiteinheit", [{}])[0].get("name", None)
                        exam["duration_type"] = exa.get("typ", None) # e.g. Vorbereituungszeit, ...
                        exam["exam_organization"] = {"organization_id": exa.get("orgeinheit", {}).get("orgeinheit", None), "role": exa.get("orgeinheit", {}).get("role", None), "name": exa.get("orgeinheit", {}).get("name", None)}

                        exam_langs = {}
                        for d in exa.get("sprache", []):
                            if isinstance(d, str):
                                continue
                            if d.get("sprache", None) not in exam_langs:
                                exam_langs[d.get("sprache", None)] = {"language_id": d.get("sprache", None), "name": d.get("name", None)}
                        exam["languages"] = [d for d in exam_langs.values()]

                        exam["exam_frequency"] = {"frequency_id": exa.get("prfhaeufigkeit", {}).get("prfhaeufigkeit", None), "name": exa.get("prfhaeufigkeit", {}).get("name", None)}
                        exam["module_part_exams"] = exa.get("modul_lv_prfs", None)
                        exams.append(exam)

                    crs["exams"] = exams
                else:
                    crs["exams"] = None
                crs["lecturer"] = c.get("dozenten", None)
                crs["workloads"] = c.get("workloads", None)

                subparts = []
                subcrss = ({} if (a := c.get("modullv_lvs", {})) is None else a).get("modullv_lv", [])
                if isinstance(subcrss, dict):
                    subcrss = [subcrss]
                for d in subcrss:
                    subpart = {}
                    subpart["id"] = d.get("modullv_lv", None)
                    subpart["semester_id"] = d.get("lv", {}).get("semesternr", None)
                    subpart["id"] = d.get("lv", {}).get("lv", None)
                    subpart["content"] = a if (a := d.get("inhalte", None)) is None or not isinstance(a, str) else a.strip()
                    subpart["ects"] = d.get("lv", {}).get("ects", None)
                    subpart["delivery_form"] = d.get("lv", {}).get("lehrangebot_art", None)
                    subpart["semester_name"] = d.get("lv", {}).get("semester", {}).get("zeugnisbez", None)
                    subpart["type"] = d.get("lv", {}).get("lvtyp", {}).get("name", None)
                    subpart["type_id"] = d.get("lv", {}).get("lvtyp", {}).get("lvtyp", None)
                    subpart["name"] = d.get("lv", {}).get("name", None)
                    subparts.append(subpart)
                crs["subparts"] = subparts

                crs["skills"] = [{"id": d.get("typid", None), "name": d.get("name", None), "knowledge": d.get("kenntnis", None), "skills": d.get("fertigkeiten", None), "competency": d.get("kompetenzen", None)} for d in ((c or {}).get("modullv_matrixs", {}) or {}).get("modullv_matrix", [])]

                # TODO: check sorted_modul_lv_prfs, modul_lv_prfs

                parts.append(crs)

            module["parts"] = parts
            mod["graded"] = True if mod.get("unbenotet", None) == 0 else False if mod.get("unbenotet", None) == 1 else None
            modules.append(module)

        new_module_group["modules"] = modules

        new_module_groups.append(new_module_group)
    new_mhb["module_groups"] = new_module_groups

    return new_mhb

if __name__ == "__main__":
    with open("xml_processing/test_cleaned.json", "r") as f:
        data = json.load(f)

    result = clean_mhb(data)
