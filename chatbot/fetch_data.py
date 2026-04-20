from database import database as db

def fetch_data() -> list[dict[str, str | int | None]]:
    """
    Fetches all well extracted modules from the database

    Returns:
        list[dict[str, str | int | None]]: A list of dictionaries containing module information.
    """
    
    query = """
    WITH a AS (SELECT
        ai.raw_module_id AS ai_raw_module_id,
        ai.title AS ai_title,
        ai.module_code AS ai_module_code,
        ai.ects AS ai_ects,
        ai.lecturer AS ai_lecturer,
        ai.contents AS ai_contents,
        ai.goals AS ai_goals,
        ai.requirements AS ai_requirements,
        ai.expense AS ai_expense,
        ai.success_requirements AS ai_success_requirements,
        ai.weekly_hours AS ai_weekly_hours,
        ai.recommended_semester AS ai_recommended_semester,
        ai.exams AS ai_exams,
        ai.module_parts AS ai_module_parts,
        modules.id AS module_id,
        modules.title AS module_title,
        modules.module_code AS module_code,
        modules.ects AS module_ects,
        modules.content AS module_content,
        modules.goals AS module_goals,
        modules.pages AS module_pages,
        modules.mhb_id AS module_mhb_id,
        raw.content AS raw_content,

        mhbs.version AS version,
        CASE
            WHEN ai.module_code IS NULL THEN 0.5
            WHEN ai.module_code = modules.module_code THEN 1
            ELSE 0
        END AS correct_module_code,
        CASE
            WHEN ai.ects IS NULL THEN 0.5
            WHEN ai.ects = modules.ects THEN 1
            ELSE 0
        END AS correct_ects,
        CASE
            WHEN ai.title IS NULL THEN 0.5
            WHEN ai.title = modules.title THEN 1
            ELSE 0
        END AS correct_title
    FROM unia.modules_ai_extracted AS ai
    JOIN unia.modules_raw AS raw ON ai.raw_module_id = raw.id
    JOIN unia.modules ON raw.mhb_id = modules.mhb_id AND raw.module_code = modules.module_code
    JOIN unia.mhbs ON modules.mhb_id = mhbs.id
    WHERE (SELECT string_agg(c::text, ', ') FROM jsonb_array_elements_text(ai.contents) as c) not ilike '%hebamme%'
    )

    SELECT DISTINCT ON (a.module_code) a.* FROM a ORDER BY a.module_code, a.correct_module_code DESC, a.correct_ects DESC, a.correct_title DESC, a.version DESC
    ;
    """

    result = db.custom_call(
        query,
        type_of_answer=db.ANSWER_TYPE.LIST_ANSWER
    )

    if result.is_error:
        raise result.error

    columns = [
        "ai_raw_module_id",
        "ai_title",
        "ai_module_code",
        "ai_ects",
        "ai_lecturer",
        "ai_contents",
        "ai_goals",
        "ai_requirements",
        "ai_expense",
        "ai_success_requirements",
        "ai_weekly_hours",
        "ai_recommended_semester",
        "ai_exams",
        "ai_module_parts",
        "module_id",
        "module_title",
        "module_code",
        "module_ects",
        "module_content",
        "module_goals",
        "module_pages",
        "module_mhb_id",
        "raw_content",
        "version",
        "correct_module_code",
        "correct_ects",
        "correct_title"
    ]

    data = [{key: value if not str(key).startswith("correct") else int(value) for key, value in zip(columns, i)} for i in result.data]

    # ordering important for the embedding creation since of weighing
    input_data = [{
        "module_code": d["module_code"] if d["module_code"] is not None else d["ai_module_code"],
        "title": d["module_title"] if d["module_title"] is not None else d["ai_title"],
        "ects": d["module_ects"] if d["module_ects"] is not None else d["ai_ects"],
        "complete_content": d["module_content"],
        "summarized_content": d["ai_contents"],
        "goals": d["module_goals"],
        "summarized_goals": d["ai_goals"],
        "requirements": d["ai_requirements"],
        "recommended_semester": d["ai_recommended_semester"],
        "module_parts": d["ai_module_parts"],
        "weekly_hours": d["ai_weekly_hours"],
        "expense": d["ai_expense"],
        "exams": d["ai_exams"],
        "success_requirements": d["ai_success_requirements"],
        "lecturer": d["ai_lecturer"],
        "version": ("Winter" if (winter := int((version := str(d["version"]))[-1]) == 1) else "Sommer") + "semester " + (year := str(d["version"])[:-1]) + (("/" + str(int(year) + 1)) if winter else "") if d["version"] is not None else None,
        "score": (d["correct_module_code"] + d["correct_ects"] + d["correct_title"]) / 3
    } for d in data]

    return input_data