"""
"""

import json
from typing import Callable


def clean_mhb(data: dict) -> dict:
    """
    clean the mhb data by removing unnecessary keys and renaming keys

    Args:
        data (dict): the mhb data to clean
    Returns:
        dict: the cleaned mhb data
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
                if str(type(i)) in retype_values.keys():
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
                    i = recursive_walk(i, remove_keys, rename_keys, retype_values, replace_values, list_key=None)
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
                if str(type(d[key])) in retype_values.keys():
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


    recursive_walk(mhb["handbuch_gruppen"]["handbuch_gruppe"], remove_keys, rename_keys, retype_values=retype_values, replace_values=replace_values)

    # print(json.dumps(mhb, indent=4)[:10000])
    # print(mhb["handbuch_gruppen"]["handbuch_gruppe"][0]["modulgruppe"]["gruppe_module"]["gruppe_modul"][0]["studien_modul"].keys())

    new_mhb = dict()
    new_mhb["id"] = mhb["modulhandbuch"]
    new_mhb["name"] = mhb["bez"]
    new_mhb["description"] = m.split(" (")[0] if (m := mhb["beschreibung"]) else None
    new_mhb["language_description"] = m.split(" (")[0] if ( m:= mhb["sprache_beschreibung"]) else None
    new_mhb["start_semester"] = mhb["semester"][0]["zeugnisbez"]
    new_mhb["mhb_pos_unclear-"] = mhb["mhb_pos"]
    new_mhb["mhb_group_id"] = mhb["orgeinheit"]["orgeinheit"]
    new_mhb["mhb_group_name"] = mhb["orgeinheit"]["bez"]
    new_mhb["module_groups"] = []

    new_module_groups = []

    language_mappings = {"sprache": "langugage_id", "name": "language"}

    for i in mhb["handbuch_gruppen"]["handbuch_gruppe"]:
        new_module_group = dict()
        new_module_group["order"] = i["reihenfolge"]
        new_module_group["id"] = i["modulgruppe"]["modulgruppe"]
        new_module_group["min_ects"] = i["modulgruppe"]["ectsmin"]
        new_module_group["max_ects"] = i["modulgruppe"]["ectsmax"]
        new_module_group["po_version_unclear-"]= i["modulgruppe"]["bezeichnung"]
        new_module_group["name_letter"] = i["modulgruppe"]["name"][0]
        new_module_group["type"] = i["modulgruppe"]["name"][2:].split(" (")[0]
        new_module_group["name"] = i["modulgruppe"]["name"].split("): ")[-1]

        if isinstance(i["modulgruppe"]["gruppe_module"]["gruppe_modul"], dict):
            i["modulgruppe"]["gruppe_module"]["gruppe_modul"] = [i["modulgruppe"]["gruppe_module"]["gruppe_modul"]]

        modules = []
        for e in i["modulgruppe"]["gruppe_module"]["gruppe_modul"]:
            module = dict()
            # important: studien_modul, ordnummer, pflicht, fachsem, gruppe_modul_art
            module["order"] = e["ordnummer"]
            module["is_mandatory"] = a if (a := e["pflicht"]) is not None and a != -1 else None if (b := e["gruppe_modul_art"].get("gruppe_modul_art", -1)) == -1 else b == 1
            module["semester"] = e["fachsem"]

            mod = e["studien_modul"]

            # TODO: check keys: ects_info, url, haeufigkeit, ects_schluessel, bemerkung_extern, bemerkung_intern, nutzer, nachhaltigkeit, sprache_nachhaltigkeit, drucken, nur_eng_drucken, sprache_haeufigkeit, modul_prfs.modulprf.schl_komp

            module["id"] = mod["studien_modul"]
            module["created_at"] = mod["zeitstempel"]
            module["module_code"] = mod["kurz_bez"]
            module["ects"] = mod["ects_punkte"]
            module["duration_in_semesters"] = mod["dauer"]
            module["weekly_hours"] = mod["sws"]
            module["min_semester"] = mod["minfachsem"]
            module["max_semester"] = mod["maxfachsem"]
            module["title"] = mod["sprache_bez"]
            module["content"] = mod["inhalte"]
            module["workload"] = mod["arbeitsaufwand"]
            module["prerequisites"] = mod["voraussetzungen"] # usually requirements
            module["success_requirements"] = mod["ects_bedingungen"]
            module["frequency"] = [{"frequency_id": c["haeufigkeit"], "frequency_name": c["name"]} for c in mod["haeufigkeit"] if isinstance(c, dict)]
            module["capacity"] = mod["kapazitaet"]
            module["retake"] = mod["wiederholung"]
            module["external_notes"] = mod["bemerkung_extern"]
            module["internal_notes"] = mod["bemerkung_intern"]
            module["lecturer"] = mod["nochzustaendig"]
            module["mandatory_proof"] = mod["pflichtnachweis"]
            module["creator"] = mod["nutzer"]
            module["module_course_combination"] = mod["modullv_kombi"]
            module["exam"] = mod["modulprf_kombi"]
            module["goals"] = mod["lernziele"]
            # module["graded"] = mod["unbenoted"] is False if mod["unbenoted"] is not None else # TODO: finish this with module_lvs
            module["international"] = mod["international"]
            module["prerequisite_language"] = mod["sprache_voraussetzungen"]
            module["notes_about_changes"] = mod["bem_aenderung"]
            module["name"] = mod["name"]
            # TODO: check removing duplicates from languages like below
            module["languages"] = [{language_mappings[k]: v for k, v in c.items() if k in ["sprache", "name"]} for c in mod["sprache"]]

            persons = mod["person"]

            module["maintainers"] = [{"person_id": c["personid"], "role": c["role"], "email": c["email"], "first_name": c["vorname"], "last_name": c["nachname"], "degree": c["akadgrad"]} for c in persons if c["personid"] is not None and c["personid"] > 0]

            sem = mod["semester"]
            start_semester = next((c for c in sem if c["role"].lower() == "semesterbybis"), None)
            start_semester = {"id": start_semester["semesternr"], "name": start_semester["zeugnisbez"], "short_name": start_semester["semester"]} if start_semester else None
            end_semester = next((c for c in sem if c["role"].lower() == "semesterbyvon"), None)
            end_semester = {"id": end_semester["semesternr"], "name": end_semester["zeugnisbez"], "short_name": end_semester["semester"]} if end_semester else None
            sem_ids = [c["id"] for c in [start_semester, end_semester] if c is not None]
            module["available_semesters"] = {"start_semester": start_semester,
                                            "end_semester": end_semester,
                                            "other_semesters": [{ "id": c["semesternr"], "name": c["zeugnisbez"], "short_name": c["semester"]} for c in sem if c["semesternr"] not in sem_ids]}
            
            module["keywords"] = mod["sorted_modul_stichworte"]
            module["usability"] = {k: v for k, v in mod["verwendbarkeit"].items() if k != "sprache_bez"}
            module["organization_owner"] = [ {"organization_id": c["orgeinheit"], "role": c["role"], "name": c["name"]} for c in mod["orgeinheit"]]
            
            # print(list(mod.keys()))
            mod_parts = mod["modul_lvs"]["modul_lv"]
            # print(json.dumps(mod_parts, indent=4))

            # TODO: maybe add to lv if more exist, but probably not
            # TODO: look at modul_lv_prfs key
            # NOTE: ignore as that is a less precisely played duplicate of exam in courses (lv)
            exam = dict()
            exa = mod["modul_prfs"]["modul_prf"]
            exam["id"] = exa["modul_prf"]
            exam["created_at"] = exa["zeitstempel"]
            exam["duration"] = exa["pruefdauer"]
            exam["graded"] = True if exa["unbenotet"] == 0 else False if exa["unbenotet"] == 1 else None
            exam["portion_of_grade"] = exa["anteil_note"]
            exam["preparation"] = exa["vorbereitung"]
            exam["lecture_duration"] = exa["vorlesung_dauer"]
            exam["deadline"] = exa["frist"]
            exam["name"] = exa["name"]
            exam["description"] = exa["description"]
            exam["type"] = exa["tptyp"]["name"]
            exam["type_id"] = exa["tptyp"]["tptyp"]
            exam["time_unit"] = exa["zeiteinheit"][0]["name"]
            exam["duration_type"] = exa["typ"] # e.g. Vorbereituungszeit, ...
            exam["exam_organization"] = {"organization_id": exa["orgeinheit"]["orgeinheit"], "role": exa["orgeinheit"]["role"], "name": exa["orgeinheit"]["name"]}

            exam_langs = dict()
            for c in exa["sprache"]:
                if c["sprache"] not in exam_langs:
                    exam_langs[c["sprache"]] = {"language_id": c["sprache"], "name": c["name"]}
            exam["languages"] = [c for c in exam_langs.values()]
            
            exam["exam_frequency"] = {"frequency_id": exa["prfhaeufigkeit"]["prfhaeufigkeit"], "name": exa["prfhaeufigkeit"]["name"]}
            exam["module_course_exams"] = exa["modul_lv_prfs"]
            
            module["exam"] = exam

            workloads = []
            if mod["workloads"] is None:
                workloads = None
            else:
                for c in mod["workloads"]["arbeitsaufwand"]:
                    workload = dict()
                    workload["in_presence"] = c["praesenz"]
                    workload["type"] = {"type_id": c["aufwand_art"]["aufwand_art"], "name": c["aufwand_art"]["name"]}
                    workload["workload_hours"] = c["arbeitsaufwand"]
                    
                    workloads.append(workload)

            module["workloads"] = workloads

            courses = []
            crss = mod["modul_lvs"]["modul_lv"]
            if isinstance(crss, dict):
                crss = [crss]
            for c in crss:
                crs = dict()
                crs["id"] = c.get("modul_lv", None)
                crs["created_at"] = c.get("zeitstempel", None)
                crs["weekly_hours"] = c.get("sws", None)
                crs["order"] = c.get("reihenfolge", None)
                crs["mandatory"] = True if c.get("pflicht", None) == 1 else False if c.get("pflicht", None) == 0 else None
                crs["ects"] = c.get("ects", None)
                crs["content"] = c.get("inhalte", None)
                crs["literature"] = c.get("literatur", None)
                crs["frequencies"] = [{"frequency_id": d["haeufigkeit"], "frequency_name": d["name"]} for d in mod["haeufigkeit"] if isinstance(d, dict)]
                crs["workload"] = c.get("arbeitsaufwand", None)
                crs["success_requirements"] = c.get("ects_bedingungen", None)
                crs["learning_methods"] = c.get("lernmethoden", None)
                crs["goals"] = c.get("lernziele", None)
                crs["name"] = c.get("name", None)
                crs_langs = dict()
                for d in c.get("sprache", []):
                    if d["sprache"] not in crs_langs:
                        crs_langs[d["sprache"]] = {"language_id": d["sprache"], "name": d["name"]}
                crs["languages"] = list(crs_langs.values())
                crs["teaching_methods"] = None if c.get("lehrformen", None) is None else {"id": c["lehrformen"]["modul_lv_form"]["modul_lv_form"], "name": c["lehrformen"]["modul_lv_form"]["name"]}

                exam = dict()
                if c.get("modul_prfs", None) is not None:
                    exa = c["modul_prfs"]["modul_prf"]
                    exam["id"] = exa["modul_prf"]
                    exam["created_at"] = exa["zeitstempel"]
                    exam["duration"] = exa["pruefdauer"]
                    exam["graded"] = True if exa["unbenotet"] == 0 else False if exa["unbenotet"] == 1 else None
                    exam["portion_of_grade"] = exa["anteil_note"]
                    exam["preparation"] = exa["vorbereitung"]
                    exam["lecture_duration"] = exa["vorlesung_dauer"]
                    exam["deadline"] = exa["frist"]
                    exam["name"] = exa["name"]
                    exam["description"] = exa["description"]
                    exam["type"] = exa["tptyp"]["name"]
                    exam["type_id"] = exa["tptyp"]["tptyp"]
                    exam["time_unit"] = exa["zeiteinheit"][0]["name"]
                    exam["duration_type"] = exa["typ"] # e.g. Vorbereituungszeit, ...
                    exam["exam_organization"] = {"organization_id": exa["orgeinheit"]["orgeinheit"], "role": exa["orgeinheit"]["role"], "name": exa["orgeinheit"]["name"]}

                    exam_langs = dict()
                    for d in exa.get("sprache", []):
                        if d["sprache"] not in exam_langs:
                            exam_langs[d["sprache"]] = {"language_id": d["sprache"], "name": d["name"]}
                    exam["languages"] = [d for d in exam_langs.values()]
                    
                    exam["exam_frequency"] = {"frequency_id": exa["prfhaeufigkeit"]["prfhaeufigkeit"], "name": exa["prfhaeufigkeit"]["name"]}
                    exam["module_course_exams"] = exa["modul_lv_prfs"]

                    crs["exam"] = exam
                else:
                    crs["exam"] = None
                crs["lecturer"] = c.get("dozenten", None)
                crs["workloads"] = c.get("workloads", None)

                subcourses = []
                subcrss = ({} if (a := c.get("modullv_lvs", {})) is None else a).get("modullv_lv", [])
                if isinstance(subcrss, dict):
                    subcrss = [subcrss]
                for d in subcrss:
                    subcourse = dict()
                    subcourse["id"] = d["modullv_lv"]
                    subcourse["semester_id"] = d["lv"]["semesternr"]
                    subcourse["id"] = d["lv"]["lv"]
                    subcourse["content"] = d["lv"]["inhalte"]
                    subcourse["ects"] = d["lv"]["ects"]
                    subcourse["delivery_form"] = d["lv"]["lehrangebot_art"]
                    subcourse["semester_name"] = d["lv"]["semester"]["zeugnisbez"]
                    subcourse["type"] = d["lv"]["lvtyp"]["name"]
                    subcourse["type_id"] = d["lv"]["lvtyp"]["lvtyp"]
                    subcourse["name"] = d["lv"]["name"]
                    subcourses.append(subcourse)
                crs["subcourses"] = subcourses

                crs["skills"] = [{"id": d["typid"], "name": d["name"], "knowledge": d["kenntnis"], "skills": d["fertigkeiten"], "competency": d["kompetenzen"]} for d in c.get("modullv_matrixs", {}).get("modullv_matrix", [])]

                # TODO: check sorted_modul_lv_prfs, modul_lv_prfs

                courses.append(crs)

            module["courses"] = courses
            mod["graded"] = True if mod["unbenotet"] == 0 else False if mod["unbenotet"] == 1 else None
            modules.append(module)

        new_module_group["modules"] = modules

        new_module_groups.append(new_module_group)
    new_mhb["module_groups"] = new_module_groups

    return new_mhb

if __name__ == "__main__":
    with open("xml_processing/test_cleaned.json", "r") as f:
        data = json.load(f)
    
    result = clean_mhb(data)