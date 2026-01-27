# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# For usage please contact the developer.
#
# This file is Copyright-protected.

# Description: extract structured module information from raw module text from the mhbs
# Status: VERSION 1.0
# FileID: Ai-ex-0001

"""
This module provides functionality to extract structured module information from raw module text using an AI model.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Any
import ollama


class exam_info(BaseModel):
    """
    exam info class for setting strict type requirements for ai model when extracting information
    about exams of a module

    Attributes:
        exam_type (str | None): type of the exam
        exam_info (list[str] | None): additional information about the exam
        duration (int | None): duration of the exam in minutes
    """

    exam_type: str | None = Field(
        default=None,
        description="""Die Art der Prüfung, z.B. Klausur, mündliche Prüfung, Hausarbeit, etc.""",
    )
    exam_info: list[str] | None = Field(
        default=None,
        description="""Zusätzliche Informationen zur Prüfung, falls vorhanden. Falls nicht vorhanden, lasse das Feld leer.""",
    )
    duration: int | None = Field(
        default=None, description="""Die Dauer der Prüfung in Minuten."""
    )


class time_info(BaseModel):
    """
    time info class for setting strict type requirements for ai model when extracting information
    about time related information of a module

    Attributes:
        activity (str | None): type of activity, e.g., lecture, exercise, self
        hours (int | None): number of hours of workload
    """

    activity: str | None = Field(
        default=None,
        description="""Die Art der Aktivität, z.B. Vorlesung, Übung, Selbststudium, etc.""",
    )
    hours: int | None = Field(
        default=None,
        description="""Der Arbeitsaufwand beschreibt, wie viele Stunden die Studierenden für das Modul aufwenden müssen.""",
    )


class ModuleInfo(BaseModel):
    """
    module info class for setting strict type requirements for ai model when extracting information
    about a module

    Attributes:
        title (str | None): title of the module
        module_code (str | None): unique module code
        ects (int | None): number of ECTS credits
        lecturer (str | None): name of the lecturer
        contents (list[str] | None): list of module contents
        goals (list[str] | None): list of learning goals
        requirements (list[str] | None): list of prerequisites
        expense (list[time_info] | int | None): workload information
        success_requirements (list[str] | None): list of success requirements
        weekly_hours (int | None): number of weekly hours
        recommended_semester (int | None): recommended semester to take the module
        exams (list[exam_info] | None): list of exam information
        module_parts (list[dict[Any, Any]] | None): list of module parts if applicable
    """

    title: str | None = Field(
        default=None,
        description="""Der Titel des Moduls. Dieser befindet sich meist in der Überschrift oder in dem Feld Titel / Name.""",
    )
    module_code: str | None = Field(
        default=None,
        description="""Der Modulcode des Moduls. Dieser ist für jedes Modul einzigartig und kann auch als ID bezeichnet werden.""",
    )
    ects: int | None = Field(
        default=None,
        description="""Die ECTS Anzahl oder die LP Anzahl oder die CP Anzahl des Moduls, das bedeutet wie viele Credit Points oder Leistungspuntke das Modul erbringt.""",
    )
    lecturer: str | None = Field(
        default=None,
        description="""Gibt an, welcher Professor, Dozent oder Vortragender die Vorlesung hält.""",
    )
    contents: list[str] | None = Field(
        default=None,
        description="""Eine Liste der Inhalte des Moduls. Diese befinden sich meist in der Kategorie Inhalte. Inhalte beschreiben die Themen des Moduls.""",
    )
    goals: list[str] | None = Field(
        default=None,
        description="""Eine Liste der Lernziele des Moduls. Diese befinden sich meist in der Kategorie Lernziele oder Ziele. Lernziele beschreiben, welche Kompetenzen und Fähigkeiten die Studierenden in dem Modul erwerben.""",
    )
    requirements: list[str] | None = Field(
        default=None,
        description="""Eine Liste der Voraussetzungen für das Modul. Diese befinden sich meist in der Kategorie Voraussetzungen oder Anforderungen. Voraussetzungen beschreiben, welche Kenntnisse oder Fähigkeiten Studierende vor dem Besuch des Moduls besitzen sollten.""",
    )
    expense: list[time_info] | int | None = Field(
        default=None,
        description="""Der Arbeitsaufwand für das Modul. Dieser kann als Liste von Stundenangaben mit Aktivitätsbeschreibung oder als Gesamtsumme in Stunden angegeben werden. Falls er detailliert als Liste angegeben werden kann, soll dies gemacht werden.""",
    )
    success_requirements: list[str] | None = Field(
        default=None,
        description="""'Eine Liste an Anforderungen, die erfüllt sein müssen, um das Modul erfolgreich abzuschließen. Es sind die Anforderungen, um die ECTS / LP / CP / Credit Points / Leistungspunkte zu erlangen. Diese befinden sich meist in der Kategorie Erfolgsanforderungen, ECTS-Bedinungen oder LP-Bedingungen.""",
    )
    weekly_hours: int | None = Field(
        default=None,
        description="""Die Anzahl der Semesterwochenstunden oder SWS oder wöchentlichen Stunden, die für das Modul aufgewendet werden müssen. Diese Angabe befindet sich meist in der Kategorie SWS oder Semesterwochenstunden, manchmal auch unter Arbeitsaufwand. Diese Angabe ist nicht das gleiche wie die Angaben in expense und darf daher unabhängig von expense angegeben werden.""",
    )
    recommended_semester: int | None = Field(
        default=None,
        description="""Das empfohlene Semester, in dem das Modul belegt werden sollte oder ab dem das Modul frühestens belegt werden sollte. Diese Angabe befindet sich meist in der Kategorie 'Empfohlenes Semester', ' Empfohlenes Fachsemester' oder Studienverlauf.""",
    )
    exams: list[exam_info] | None = Field(
        default=None,
        description="""Eine Liste von Prüfungen, die im Modul stattfinden. Jede Prüfung enthält Informationen über die Art der Prüfung, die Dauer und den Anteil an der Gesamtnote.""",
    )
    module_parts: None | list[dict[Any, Any]] = Field(
        default=None,
        description="""Eine Liste von Modulteilen, falls das Modul aus mehreren Teilen besteht. Diese befinden sich meist in der Kategorie Modulteile oder Modulbestandteile. Diese Angabe ist nur selten vorhanden. Jeder Modulteil besteht aus einem Dictionary mit values aus den Informationen zu dem Modul und den keys, die daraus hervorgehen. Falls sie nicht vorhanden ist, lasse das Feld leer.""",
    )


valid_full_info = {
    "title": "Gesundheits-/ Hebammenwissenschaftliches Denken und Methodenkompetenz III",
    "module_code": "MED-0113",
    "ects": 5,
    "lecturer": " Univ.-Prof. Dr.oec.troph.habil. Thorsten Terlecki",
    "contents": [
        "Deutsches Gesundheitssystem Ordnung: politische und rechtliche Struktur der Bundesrepublik, politische Meinungsbildung im hebammenwissenschaftlichen Kontext, politisches System und Wirtschaftsordnungsmodelle, soziale Sicherung, internationaler Vergleich",
        "Entwicklung, Struktur und Prinzipen des deutschen Gesundheits- und Pflegesystems",
        "Bedeutung und Leistungen der Gesetzlichen Krankenversicherung nach SGB V",
        "Krankenhäuser als wesentliche Leistungserbringer: Organisation, Leistung und Finanzierung;",
        "Leistungsdaten, Ausstattung und wirtschaftliche Betriebsführung im Krankenhaus",
        "Rehabilitationssystem mit Bezug zur Hebammentätigkeit",
        "Die Hebamme im sektoralen Gesundheitssystem und als Akteurin im Gesundheitswesen",
    ],
    "goals": [
        "die Grundstrukturen des deutschen Gesundheitssystems darstellen",
        "die Normengeber des Gesundheitssystems mit Fokus Hebammentätigkeit und Geburtshilfe benennen",
        "Rollen und Funktionen der Hebamme im deutschen Gesundheitswesen darstellen",
        "den Rehabilitationsgedanken reflektieren und in der Hebammentätigkeit umsetzen",
    ],
    "requirements": ["Zulassung zum Studium der Hebammenwissenschaft"],
    "expense": [
        {"activity": "Teilnahme an Lehrveranstaltungen (Präsenzstudium)", "hours": 42},
        {
            "activity": "Vor- und Nachbereitung des Stoffes inkl. Prüfungsvorbereitung (Selbststudium)",
            "hours": 108,
        },
    ],
    "success_requirements": ["Bestehen der Modulprüfung"],
    "weekly_hours": 3,
    "recommended_semester": 2,
    "exams": [
        {
            "exam_type": "Klausur",
            "exam_info": [
                "Antwortformat: Antwort-Wahl-Verfahren, benotet",
                "Die Anmeldung zu jeder einzelnen Prüfung und zum Wiederholungsversuch erfolgt nicht automatisch und muss selbstständig von Ihnen durchgeführt werden. Die Termine der Prüfungen und Wiederholungsprüfung sowie die Frist zur Anmeldung werden Ihnen rechtzeitig mitgeteilt.",
            ],
            "duration": 32,
        }
    ],
    "module_parts": [
        {
            "title": "Gesundheits- und Versorgungssystem im Kontext von Hebammenwesen und -wissenschaft",
            "language": "deutsch",
            "teaching_methods": [
                "Vorlesung",
                "Gruppenarbeit",
                "Diskussion",
                "Präsentation",
            ],
        }
    ],
}


definition_model_position = f"""
Sie sind ein Extraktionsmodell, das Informationen aus Modulhandbüchern extrahiert und in einem strukturierten JSON-Format zurückgibt. Deine Hauptsprache ist Deutsch, aber du beherrscht auch Englisch. Es gibt keine Toleranz für Halluzination oder dem Erfinden zusätzlicher Informationen. Sie verwenden ausschließlich Daten aus den mitgelieferten Daten.
Wiederholungen sind erlaubt, insofern sie sinnvoll sind. Beispielsweise unterscheiden sich die SWS-Angaben für das Modul und die Modulteile, weswegen die Gesamtanzahl unter weekly_hours und die Aufteilung in den Modulen angegeben werden soll.
Falls Informationen in anderen Bereichen teilweise sinnvoll sind, soll der dort vorkommende Teil ebenfalls angegeben werden. Ein Beispiel ist das Feld Inhalt.

Absoulte Regeln:
1. Antworte nur mit dem JSON-Objekt, das die extrahierten Informationen enthält. Keine zusätzlichen Erklärungen oder Kommentare.
2. Wenn Informationen für ein bestimmtes Feld nicht verfügbar sind, lasse das Feld leer oder setze es auf null.
3. Vermute niemals Informationen und generiere niemals Informationen.
4. Verwende die bereitgestellten Daten ausschließlich zur Extraktion der Informationen. Erfinde keine zusätzlichen Details oder Informationen.
5. Es ist besser, immer null zurückzugeben, als ein einziges Mal zu raten.


Erlaubt:
    {valid_full_info}

Wichtig: Gebe nur Informationen wieder. Falls Informationen fehlen, lasse das entsprechende Feld leer.
"""


def extract_module_info(
    module_text: str,
    local: bool = True,
    model: str = "llama3.2:3b",  # "llama3.3:70b"
) -> ModuleInfo:
    """
    Extract structured module information from raw module text using an AI model.
    Args:
        module_text (str): The raw text of the module from which to extract information.
        local (bool): Whether to use a local model or a remote one. Defaults to True.
        model (str): Specify the AI model to use.

    Returns:
        ModuleInfo: A Pydantic model containing the extracted module information.
    """
    additional_params = (
        {"host": "http://misit-183.informatik.uni-augsburg.de:11434/"}
        if not local
        else {}
    )
    try:
        response = ollama.chat(
            **additional_params,
            model=model,
            messages=[
                {"role": "system", "content": definition_model_position},
                {"role": "user", "content": f"Extract data from: \n\n{module_text}"},
            ],
            format=ModuleInfo.model_json_schema(),
            options={
                "temperature": 0,
                "top_p": 0.1,
                "repeat_penalty": 1,  # 0.8
            },
        )
        module_info = ModuleInfo.model_validate_json(response["message"]["content"])
    except Exception as e:
        raise

    return module_info


if __name__ == "__main__":
    with open("sample_module.txt", "r", encoding="utf-8") as f:
        sample_text = f.read()

    extracted_info = extract_module_info(sample_text)
    print(extracted_info.model_dump_json(indent=4, ensure_ascii=False))
