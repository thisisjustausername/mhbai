import asyncio
from mhbai.student_counselor.langgraph.tools import (
    get_klausur,
    get_klausur_by_mongodb_id,
    get_modul,
    get_modul_by_mongodb_id,
    get_modulhandbuch_by_mongodb_id,
    get_studiengang_modulhandbuch
)


result = asyncio.run(get_klausur.ainvoke(
    {'name': 'Analysis 1 schriftlich',
    'graded': True}
))

result = asyncio.run(
    get_modul.ainvoke(
        {'name': 'Analysis 1',
            'weekly_hours': (0, 500)}
    )
)

result = asyncio.run(get_studiengang_modulhandbuch.ainvoke(
    {'name': 'Informatik',
    'description': '2023',
    }))

result = '\n\n--- Neues Result ---\n\n'.join(result)
print(result)
