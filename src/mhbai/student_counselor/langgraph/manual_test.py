import asyncio
from mhbai.student_counselor.langgraph.tools import (
    get_klausur,
    get_klausur_by_mongodb_id,
    get_modul,
    get_modul_by_mongodb_id,
    get_modulhandbuch_by_mongodb_id,
    get_studiengang_modulhandbuch
)
import json
'''
result = asyncio.run(get_klausur.ainvoke(
    {'name': 'Analysis 1 schriftlich',
    'graded': True}
))
'''
result = asyncio.run(
    get_modul.ainvoke(
        {'module_code': 'GES-0001',
            'name': 'Geschichte',
            'weekly_hours': (0, 500)}
    )
)
'''
result = asyncio.run(get_studiengang_modulhandbuch.ainvoke(
    {'name': 'Data Science',
    'start_semester': (20240, 20271)
    }))


result = asyncio.run(get_studiengang_modulhandbuch.ainvoke(
    {'name': 'Geschichte Nebenfach', 'k': 100}))
'''
print([i['name'] for i in json.loads(result)])
