
from typing import Any
from pydantic import BaseModel, Field


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
        description="Die Art der Prüfung, z.B. Klausur, mündliche Prüfung, Hausarbeit, etc.",
    )
    exam_info: list[str] | None = Field(
        default=None,
        description="Zusätzliche Informationen zur Prüfung, falls vorhanden. Falls nicht vorhanden, lasse das Feld leer.",
    )
    duration: int | None = Field(
        default=None,
        description="Die Dauer der Prüfung in Minuten.",
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
        description="Die Art der Aktivität, z.B. Vorlesung, Übung, Selbststudium, etc.",
    )
    hours: int | None = Field(
        default=None,
        description="Der Arbeitsaufwand beschreibt, wie viele Stunden die Studierenden für das Modul aufwenden müssen.",
    )

class ModuleInfo(BaseModel):
    """
    module info class for setting strict type requirements for ai model when extracting information
    about a module

    Attributes:
        title (str | None): title of the module; often it is found under names like Modulcode
        module_code (str | None): unique module code; often it is found under names like Titel
        ects (int | None): number of ECTS credits; often it is found under names like ECTS, LP, CP, Credit Points, Leistungspunkte
        lecturer (str | None): name of the lecturer; often it is found under names like Dozent, Professor, Modulverantwortlicher, Lehrperson, Dozent, Dozent*in
        contents (list[str] | None): list of module contents; often it is found under names like Inhalt, Beschreibung
        goals (list[str] | None): list of learning goals; often it is found under names like Ziele, Lernziele, Kompetenzen
        requirements (list[str] | None): list of prerequisites; often it is found under names like Anforderungen, Voraussetzungen, Vorkenntnisse
        expense (list[time_info] | int | None): workload information; often it is found under names like Arbeitsaufwand, Aufwand
        success_requirements (list[str] | None): list of success requirements; often it is found under names like Erfolgsvoraussetzungen, Abchlusskriterien
        weekly_hours (int | None): number of weekly hours; often it is found under names like SWS, Semesterwochenstunden, Wöchentliche Stunden, Wochenstunden, Aufwand
        recommended_semester (int | None): recommended semester to take the module; often it is found under names like Empfohlenes Semester, Empfohlenes Fachsemester
        exams (list[exam_info] | None): list of exam information; often it is found under names like Prüfungen, Prüfungsleistungen, Prüfungsformen
        module_parts (list[dict[Any, Any]] | None): list of module parts if applicable; often it is found under names like Modulteile, Modulbestandteile
    """

    title: str | None = Field(
        default=None,
        description="Der Titel des Moduls. Dieser befindet sich meist in der Überschrift oder in dem Feld Titel / Name.",
    )
    module_code: str | None = Field(
        default=None,
        description="Der Modulcode des Moduls. Dieser ist für jedes Modul einzigartig und kann auch als ID oder Modulcode bezeichnet werden.",
    )
    ects: int | None = Field(
        default=None,
        description="Die ECTS Anzahl oder die LP Anzahl oder die CP Anzahl des Moduls, das bedeutet wie viele Credit Points oder Leistungspuntke das Modul erbringt.",
    )
    lecturer: str | None = Field(
        default=None,
        description="Gibt an, welcher Professor, Dozent, Vortragender oder Modulverantwortlicher die Vorlesung hält.",
    )
    contents: list[str] | None = Field(
        default=None,
        description="Eine Liste der Inhalte des Moduls. Diese befinden sich meist in der Kategorie Inhalte oder Beschreibung. Inhalte beschreiben die Themen des Moduls.",
    )
    goals: list[str] | None = Field(
        default=None,
        description="Eine Liste der Lernziele des Moduls. Diese befinden sich meist in der Kategorie Lernziele, Ziele oder Kompetenzen. Lernziele beschreiben, welche Kompetenzen und Fähigkeiten die Studierenden in dem Modul erwerben.",
    )
    requirements: list[str] | None = Field(
        default=None,
        description="Eine Liste der Voraussetzungen für das Modul. Diese befinden sich meist in der Kategorie Voraussetzungen, Anforderungen oder Vorkenntnisse. Voraussetzungen beschreiben, welche Kenntnisse oder Fähigkeiten Studierende vor dem Besuch des Moduls besitzen sollten.",
    )
    expense: list[time_info] | int | None = Field(
        default=None,
        description="Der Arbeitsaufwand für das Modul. Dieser kann als Liste von Stundenangaben mit Aktivitätsbeschreibung oder als Gesamtsumme in Stunden angegeben werden. Falls er detailliert als Liste angegeben werden kann, soll dies gemacht werden. Meist kann dieser Punkt unter Aufwand oder Arbeitsaufwand aufgefunden werden.",
    )
    success_requirements: list[str] | None = Field(
        default=None,
        description="Eine Liste an Anforderungen, die erfüllt sein müssen, um das Modul erfolgreich abzuschließen. Es sind die Anforderungen, um die ECTS / LP / CP / Credit Points / Leistungspunkte zu erlangen. Diese befinden sich meist in der Kategorie Erfolgsanforderungen, ECTS-Bedinungen oder LP-Bedingungen. Manchmal sind auch Namen wie Erfolgsvoraussetzungen oder Abschlusskriterien zu finden.",
    )
    weekly_hours: int | None = Field(
        default=None,
        description="Die Anzahl der Semesterwochenstunden oder SWS oder wöchentlichen Stunden, die für das Modul aufgewendet werden müssen. Diese Angabe befindet sich meist in der Kategorie SWS oder Semesterwochenstunden, manchmal auch unter Arbeitsaufwand. Diese Angabe ist nicht das gleiche wie die Angaben in expense und darf daher unabhängig von expense angegeben werden.",
    )
    recommended_semester: int | None = Field(
        default=None,
        description="Das empfohlene Semester, in dem das Modul belegt werden sollte oder ab dem das Modul frühestens belegt werden sollte. Diese Angabe befindet sich meist in der Kategorie 'Empfohlenes Semester', ' Empfohlenes Fachsemester' oder Studienverlauf.",
    )
    exams: list[exam_info] | None = Field(
        default=None,
        description="Eine Liste von Prüfungen, die im Modul stattfinden. Jede Prüfung enthält Informationen über die Art der Prüfung, die Dauer und den Anteil an der Gesamtnote.",
    )
    module_parts: None | list[dict[Any, Any]] = Field(
        default=None,
        description="Eine Liste von Modulteilen, falls das Modul aus mehreren Teilen besteht. Diese befinden sich meist in der Kategorie Modulteile, Modulbestandteile, Prüfungen, Prüfungsleistungen oder Prüfungsformen. Diese Angabe ist nur selten vorhanden. Jeder Modulteil besteht aus einem Dictionary mit values aus den Informationen zu dem Modul und den keys, die daraus hervorgehen. Falls sie nicht vorhanden ist, lasse das Feld leer.",
    )
    module_group: None | str = Field(
        default=None,
        description="Die Modulgruppe, zu der das Modul gehört. Die Modulgruppe ist eine Gruppe, der das Modul im Inhaltsverzeichnis zugeordnet ist. Im Inhaltsverzeichnis steht das Modul unter einer Überschrift mit Modulgruppe. Eine Modulgruppe beschreibt einen thematischen Block in einem Studiengang. Beispiele sind 'Seminar' oder 'Wahlbereich'."
    )

class ModuleHandbook(BaseModel):
    """
    module handbook class for setting strict type requirements for ai model when extracting information
    about a module handbook

    Attributes:
        modules (list[ModuleInfo] | None): list of module information
    """

    modules: list[ModuleInfo] | None = Field(
        default=None,
        description="Eine Liste von Modulen, die im Modulhandbuch enthalten sind. Jedes Modul enthält Informationen zu einem bestimmten Modul.",
    )

translate_keys = {
    "module_code": "Modulcode",
    "title": "Titel",
    "ects": "ECTS",
    "complete_content": "Vollständiger Inhalt",
    "summarized_content": "Zusammenfassung des Inhalts",
    "goals": "Ziele",
    "summarized_goals": "Zusammenfassung der Ziele",
    "requirements": "Anforderungen",
    "recommended_semester": "Empfohlenes Semester",
    "module_parts": "Modulteile",
    "weekly_hours": "Wöchentliche Stunden",
    "expense": "Kosten",
    "exams": "Prüfungen",
    "success_requirements": "Erfolgsvoraussetzungen",
    "lecturer": "Dozent",
    "version": "Version",
    "module_group": "Modulgruppe"
}
key_mapping: str = "\n".join(f"{value}, ...: {key}" for key, value in translate_keys.items())

module_handbook = {
    "modules": [
        {
            "title": "string or null"
        }
    ]
}