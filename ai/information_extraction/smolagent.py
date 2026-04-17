from smolagents import CodeAgent, LiteLLMModel
from ai.information_extraction.data_template import exam_info, time_info, ModuleInfo, ModuleHandbook
from .tools import FinalAnswerTool
# Initialize a model (using Hugging Face Inference API)

model = LiteLLMModel(model_id="ollama_chat/gemma4:31b")
model = LiteLLMModel(model_id="ollama_chat/qwen3.6:35b-a3b")

# Create an agent with no tools
agent = CodeAgent(
    tools=[FinalAnswerTool()],
    additional_authorized_imports=["json", "pydantic", "typing"],
    model=model)

prompt = '''
Sie sind ein Extraktionsmodell, das Informationen aus Modulhandbüchern extrahiert und in einem strukturierten JSON-Format zurückgibt. Ihre Hauptsprache ist Deutsch, aber Sie beherrschen auch Englisch. Es gibt keine Toleranz für Halluzination oder dem Erfinden zusätzlicher Informationen. Sie verwenden ausschließlich Informationen aus den mitgelieferten Daten.
Hintergrundwissen ist ausschließlich für die Klassifikation der Daten in die angegebenen Kategorien erlaubt, allerdings nicht nötig.
Wiederholungen sind erlaubt, insofern sie sinnvoll sind. Beispielsweise unterscheiden sich die SWS-Angaben für das Modul und die Modulteile, weswegen die Gesamtanzahl unter weekly_hours und die Aufteilung in den Modulen angegeben werden soll.
Falls Informationen in anderen Bereichen teilweise sinnvoll sind, soll der dort vorkommende Teil ebenfalls angegeben werden. Ein Beispiel ist das Feld Inhalt.
Beachte, dass der Text ein ganzes Modulhandbuch widergibt, das aus mehreren aufeinanderfolgenden Modulen besteht. Das bedeutet, dass das Modulhandbuch ein Inhaltsverzeichnis mit allen Modultiteln und der Reihenfolge der Module enthält. Endet ein Modul, so beginnnt anschließend ein neues. Ein Modul ist in sich zusammenhängend.
Teilweise werden Module im Inhaltsverzeichnis in Modulgruppen zusammengefasst.
Der Aufbau eines Modulhandbuchs lässt sich vereinfacht meist folgendermaßen darstellen:
1. Inhaltsverzeichnis mit allen Modultiteln und der Reihenfolge der Module
2. Modul 1
3. Modul 2
...

Absolute Regeln:
1. Antworte nur mit dem JSON-Objekt, das die extrahierten Informationen enthält. Keine zusätzlichen Erklärungen oder Kommentare.
2. Wenn Informationen für ein bestimmtes Feld nicht verfügbar sind, lasse das Feld leer oder setze es auf null.
3. Vermute niemals Informationen und generiere niemals Informationen.
4. Verwende die bereitgestellten Daten ausschließlich zur Extraktion der Informationen. Erfinde keine zusätzlichen Details oder Informationen.
5. Es ist besser, immer null zurückzugeben, als ein einziges Mal zu raten.
6. Dein Code soll in Folgendem Format ausgegeben werden: 
            <code>
            # Your python code here
            </code>

Wichtig: Gebe nur Informationen wieder. Falls Informationen fehlen, lasse das entsprechende Feld leer.

Der Input als Modulhandbuch befindet sich im Markdown-Format. Die Formatierung ist noch größtenteils erhalten, allerdings nicht vollständig und teilweise irreführend.

Tools:
Rufe final_answer(data) mit data als dictionary, nicht als string, auf.

Output-Format:
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

Modulhandbuch:
\"\"\"
{module_handbook}
\"\"\"
'''

md_path = "ai/information_extraction/test-docling.md"
with open(md_path, "r") as f:
    module_handbook = f.read()

full_prompt = prompt.format(module_handbook=module_handbook)

result = agent.run(full_prompt)
print(result)