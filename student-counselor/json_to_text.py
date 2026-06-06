import os
import json


with open("student-counselor/course_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)


study_programs = []
lens = []
for i in data:
    output = f"""Studiengang: {i['Name']}
Abschluss: {i['Studienabschluss']}{'\nRegelstudienzeit: ' + d if (d := i.get('Regelstudienzeit', None)) is not None else ''}
Zulassungsmodus: {i['Zulassungsmodus']}
Unterrichtssprache: {i['Unterrichtssprache']}{('\nStudienform: ' + d) if (d := i.get('Studienform', None)) is not None else ''}
Studienbeginn: {i['Studienbeginn']}{(('\nBewerbungsfrist: ' + d) if (d := ' / '.join([e for e in ['Wintersemester: ' + i.get('Bewerbungsschluss Wintersemester', ''), 'Sommersemester: ' + i.get('Bewerbungsschluss Sommersemester', '')] if e not in ["Wintersemester: ", "Sommersemester: "]])) != '' else '') if i['Zulassungsmodus'].strip().lower() != 'zulassungsfrei' else ''}
Deutschkenntnisse: {i['Deutschkenntnisse (Mindestanforderungen)']}
Inhalt: {i['content']}
Perspektiven: {', '.join(i['perspectives'])}"""
    study_programs.append((i, output))

with open("student-counselor/info-cards.json", "w") as f:
    json.dump(study_programs, f, indent=4, ensure_ascii=True)

print(study_programs[0])
