#
# This file is part of mhbai.
#
# For usage please contact the developer.
#
# This file is Copyright-protected.

# Description: extract modules from module handbooks
# Status: PROTOTYPING
# FileID: Ai-ex-0003

"""
extract modules from module handbooks
"""

import pdfplumber
import re
import ollama
from pydantic import BaseModel


prompt = '''
Sie sind ein Extraktionsmodell, das Daten aufteilt. In Folgender PDF sind Module eines Modulhandbuchs. Am Anfang steht meist ein Inhaltsverzeichnis, danach beginnen die Module. Sie müssen die PDF in Module unterteilen. Jedes Modul ist zusammenhängend. Ignorieren Sie das Inhaltsverzecihnis. Ihre Ausgabe ist der Text 1:1 wie in der Angabe nur als Liste unterteilt in einzelne Module. Jedes Modul hat einen eigenen Modul-Code.
Insgesamt soll die Ausgabe im JSON-Format list[str] sein.

Beispielausgabe: 
    [
    """
    Modul LMZ-1713: ZQ Populäre Musik: Fachwissenschaftliche Ver- ECTS/LP: 0
    tiefung
    Version 1.0.0
    Modulverantwortliche/r:
    N.N.
    Voraussetzungen:                            ECTS/LP-Bedingungen:
    keine                                       Bestehen der Modulprüfung
    Angebotshäufigkeit:   Empfohlenes Fachsemester: Minimale Dauer des Moduls:
    jedes Semester        6. - 7.               2 Semester
    SWS:                  Wiederholbarkeit:
    4                     siehe PO des Studiengangs
    Modulteile
    Modulteil: Geschichte der populären Musik
    Lehrformen: Seminar, Vorlesung + Übung
    Sprache: Deutsch
    SWS: 2
    Lernziele:
    Der/die Studierende verfügt über berufsfeldspezifische Kenntnisse im Hinblick auf historische, musikalische und
    soziokulturelle Bedingungen und Entwicklungen der Populären Musik.
    Inhalte:
    Historische, musikalische und soziokulturelle Aspekte der Populären Musik.
    Modulteil: Musikmedien, Live- und Studiotechnik
    Lehrformen: Seminar, Vorlesung + Übung
    Sprache: Deutsch
    SWS: 4
    Lernziele:
    Der/die Studierende verfügt über berufsfeldspezifische Kenntnisse und Kompetenzen im Umgang mit
    Musikmedien, Live- und Studiotechnik.
    Inhalte:
    Theoretische und praktische Grundlagen des Umgangs mit Musikmedien, Live- und Studiotechnik.
    """, 
    """
    Modul LMZ-1714: ZQ Populäre Musik: Künstlerische und metho- ECTS/LP: 0
    dische Kompetenzen
    Version 1.0.0
    Modulverantwortliche/r:
    N.N.
    Voraussetzungen:                            ECTS/LP-Bedingungen:
    keine                                       Bestehen der Modulprüfung
    Angebotshäufigkeit:   Empfohlenes Fachsemester: Minimale Dauer des Moduls:
    jedes Semester        5. - 6.               2 Semester
    SWS:                  Wiederholbarkeit:
    5                     siehe PO des Studiengangs
    Modulteile
    Modulteil: Ensemblespiel/Ensembleleitung
    Lehrformen: Übung
    Sprache: Deutsch
    SWS: 4
    Lernziele:
    Der/die Studierende verfügt über berufsfeldspezifische Kompetenzen im
    Bereich Ensemblespiel; Kenntnisse und Kompetenzen in den Bereichen
    Ensembleleitung, Improvisation und Rhythmik.
    Inhalte:
    Aktive Mitwirkung am Ensemblespiel, Umgang mit Bandinstrumentarium
    und Musikelektronik; Vermittlungsformen Populärer Musik im Bereich
    des Ensemblespiels.
    Modulteil: Improvisation/Rhythmik
    Lehrformen: Übung
    Sprache: Deutsch
    SWS: 1
    Lernziele:
    Der/die Studierende verfügt über berufsfeldspezifische Kenntnisse und
    Kompetenzen in den Bereichen Improvisation und Rhythmik.
    Inhalte:
    mprovisationsformen und -modelle im Bereich Populärer Musik sowie
    deren stiladäquate Anwendung und Vermittlung; rhythmische/
    bewegungsorientierte Auseinandersetzung mit Populärer Musik
    """, 
    """Modul LMZ-1715: ZQ Populäre Musik: Musiktheorie und Satztech- ECTS/LP: 0
    nik
    Version 1.0.0
    Modulverantwortliche/r:
    N.N.
    Voraussetzungen:                            ECTS/LP-Bedingungen:
    keine                                       Bestehen der Modulprüfung
    Angebotshäufigkeit:   Empfohlenes Fachsemester: Minimale Dauer des Moduls:
    jedes Semester        8.                    2 Semester
    SWS:                  Wiederholbarkeit:
    2                     siehe PO des Studiengangs
    Modulteile
    Modulteil: Jazz-/Pop- Harmonielehre und Arrangement
    Lehrformen: Übung
    Sprache: Deutsch
    SWS: 2
    Lernziele:
    Berufsfeldspezifische Kenntnisse und Kompetenzen in den Bereichen Musiktheorie und Satztechnik im Kontext
    Populärer Musik.
    Inhalte:
    Musiktheoretische und satztechnische Kenntnisse und Fertigkeiten im Bereich Populärer Musik.
    """
]
'''

from pydantic import BaseModel
import ollama


class ModulesList(BaseModel):
    extracted_data: list[str]


# def extract_raw_modules(pdf_path: str) -> list[str]:

full_text = []
with pdfplumber.open("pdfs/1.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text(x_tolerance=2, y_tolerance=2, layout=True)
        if text:
            full_text.append(text)

full_text = [t for t in full_text if t.strip() != ""]
final_text = "\n\n".join(full_text)
final_text = re.sub(r"\s*\n\s*", "\n", final_text)


class ModuleExtraction(BaseModel):
    modules: list[str]


response = ollama.chat(
    model="llama3.3:70b",
    messages=[
        {
            "role": "system",
            "content": """Sie sind ein Extraktionsmodell, das Daten aufteilt. 
            In Folgender PDF sind Module eines Modulhandbuchs. 
            Am Anfang steht meist ein Inhaltsverzeichnis, danach beginnen die Module. 
            Sie müssen die PDF in Module unterteilen. 
            Jedes Modul ist zusammenhängend. 
            Ignorieren Sie das Inhaltsverzeichnis. 
            Ihre Ausgabe ist der Text 1:1 wie in der Angabe nur als Liste unterteilt in einzelne Module. 
            Jedes Modul hat einen eigenen Modul-Code.""",
        },
        {"role": "user", "content": f"Extract data from: \n\n{full_text}"},
    ],
    format=ModuleExtraction.model_json_schema(),
    options={
        "temperature": 0,
        "top_p": 0.1,
        "repeat_penalty": 1.1,  # Changed from 0.8 (should be > 1)
    },
)

# Access the response
print(response["message"]["content"])
