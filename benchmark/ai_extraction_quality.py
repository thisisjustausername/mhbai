import json
from tabulate import tabulate
from database import database as db

query = """
SELECT 
    ai.raw_module_id, 
    ai.title, 
    ai.module_code, 
    ai.ects, 
    ai.lecturer, 
    ai.contents, 
    ai.goals, 
    ai.requirements, 
    ai.expense, 
    ai.success_requirements, 
    ai.weekly_hours, 
    ai.recommended_semester, 
    ai.exams, 
    ai.module_parts, 

    modules.id AS module_id, 
    modules.title AS module_title, 
    modules.module_code AS module_code, 
    modules.ects AS module_ects, 
    modules.content AS module_content, 
    modules.goals AS module_goals, 
    modules.pages AS module_pages, 
    modules.mhb_id AS module_mhb_id, 

    raw.content AS raw_content,

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
JOIN unia.modules AS modules ON raw.mhb_id = modules.mhb_id AND raw.module_code = modules.module_code
ORDER BY raw.mhb_id;
"""

cursor = db.connect()
result = db.custom_call(
    cursor=cursor,
    query=query,
    type_of_answer=db.ANSWER_TYPE.LIST_ANSWER,
    variables=None
)

if result.is_error:
    raise Exception(f"Error fetching data: {result.error}")

print(overall := len(result.data))
print(valid := sum([1 for item in result.data if item[-1] >= 0.5 and item[-2] >= 0.5 and item[-3] >= 0.5]))
print(complete := sum([1 for item in result.data if item[-1] == 1 and item[-2] == 1 and item[-3] == 1]))


print(f"Valid data: {valid / overall * 100:.2f}%")
print(f"Complete data: {complete / overall * 100:.2f}%")