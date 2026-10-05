'''
Create tools for searching and retrieving information about study programs, modules, and exams from the internal information cards of the University of Augsburg.
'''

import os
import re
from dataclasses import dataclass, field
from typing import Literal
from urllib.parse import urljoin

import html_to_markdown as htm
import httpx
from bson.objectid import ObjectId
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from pymongo import MongoClient

from mhbai.mongo_db.init_vector_search import (
    bm25_keys,
    embedded_keys,
    embedded_keys_paths,
)

embedded_keys_paths = embedded_keys_paths.copy()

mdl = 'qwen3.8:27b'

################################################################
'''
Initialize vector database and model
'''
################################################################

embeddings = OllamaEmbeddings(model='qwen3-embedding')
# TODO: fix path to make it not user-dependent
db = Chroma(
            persist_directory=os.path.expanduser('~/mhbai/src/mhbai/student_counselor/chroma_db'),
            embedding_function=embeddings,
        )


load_dotenv()  # Load environment variables from .env file

# %% Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/', authSource='unia', username='unia-search-ai', password=os.getenv('MONGO_DB_UNIA_SEARCH_AI_PASSWORD'))
mongo_db = client['unia']
mhbs_db = mongo_db['mhbs']
modules_db = mongo_db['modules']
exams_db = mongo_db['exams']

options = htm.ConversionOptions(exclude_selectors=['script', 'style', 'noscript', 'footer', 'nav'])

################################################################
'''
Create tools
'''
################################################################

@tool
async def search_studiengang(query: str, k: int = 5) -> str:
    '''
    Durchsucht die internen Informationskarten für Studiengängen nach Studiengangsinformationen, Inhalten, Zulassungsvoraussetzungen (NC) und weiteren studiengangsspezifischen Fragen.
    Du kannst immer nur nach EINEM Studiengang pro Anfrage suchen. Für mehrere Studiengänge stelle mehrere Anfragen. Stelle die Anfragen NACHEINANDER, sonst treten Fehler auf. Sende immer nur eine Suchanfrage und warte auf die Antwort bevor du die nächste Anfrage sendest.
    Du kannst mit und nach Infos in folgenden Bereichen suchen:
        * Studiengangsname
        * Inhalt
        * Berufsperspektiven
        * Ziele
        * Regelstudienzeit
        * Teil- / Vollzeitstudium
        * Zulassungsmodus
        * Studienbeginn
        * Unterrichtssprache
        * gefordertes Deutschniveau
    Es wird empfohlen, den Studiengangsnamen zu suchen, je nach Anfrage können auch die anderen Bereiche abgefragt werden.

    Args:
        query (str): Die Suchanfrage, die Informationen zu einem Studiengang oder studiengangsbezogenen Fragen enthält.
        k (int): Die Anzahl der zurückzugebenden relevanten Ergebnisse.

    Returns:
        str: Die relevantesten Informationen aus den Informationskarten, die der Anfrage entsprechen. Wenn keine relevanten Informationen gefunden werden, wird eine entsprechende Nachricht zurückgegeben. Es sind IMMER Informationen zu Studiengangsname, Inhalt, Berufsperspektiven, Ziele, Regelstudienzeit, Teil- / Vollzeitstudium, Zulassungsmodus, Studienbeginn, Unterrichtssprache, gefordertes Deutschniveau enthalten.
    '''
    matches = db.similarity_search(query, k=k)

    if not matches:
        return 'Keine passenden Informationen gefunden.'
    return '\n\n'.join(
        [
            f'Treffer {index + 1}:\n'
            f'Studiengang: {match.metadata.get('Studiengang', 'unbekannt')}\n'
            f'Inhalt: {match.page_content}\n'
            f'Metadaten: {match.metadata}'
            for index, match in enumerate(matches)
        ]
    )


def _build_vector_search(index: str, embedding: list[float], k: int, filters: list[dict] | None):
    return {
        '$vectorSearch': {
            'queryVector': embedding,
            'path': index,
            'limit': k,
            **({'filters': filters} if filters else {})
        }
    }


def _create_filter(attribute: int | bool | tuple[int | None, int | None], lexico_search_field: None | str = None) -> int | bool | dict[str, int] | dict[str, dict[str, str | int]]:
    '''
    Creates a filter for the given attribute for mongodb search.

    Args:
        attribute (int | bool | tuple[int | None, int | None]): The value to filter for
        lexico_search_field (None | str): The field to filter for if using lexicographical search
    Returns:
        int | bool | dict[str, int]: The query then passed into the filter
    '''
    if isinstance(attribute, int): # NOTE: also returns True for bool
        if not lexico_search_field:
            return attribute
        return {'equals': {'path': lexico_search_field, 'value': attribute}}
    if isinstance(attribute, tuple):
        if not lexico_search_field:
            return {f: v for f, v in zip(['$gte', '$lte'], attribute) if v is not None}
        return {
            'range': {
                'path': lexico_search_field,
                **{f: v for f, v in zip(['gte', 'lte'], attribute) if v is not None}
                    }
        }
    # TODO: finish implementation for lists
    if isinstance(attribute, list):
        raise NotImplementedError('Currently only int, bool, and tuple[int, int] are implemented for filters. Lists are not yet supported.')


def _create_vector_search(attribs: dict, rename_keys: dict, bm25_keys: list[str], weights: dict, k: int) -> list[dict]:
    '''
    Creates a vector search for the given attributes for mongodb search.
    Note: If further selection is needed still call _create_vector_search and append it to the returned list of dicts, in case that works.

    Args:
        attribs (dict): The attributes to search for with values
        rename_keys (dict): The keys to rename for the vector search
        bm25_keys: The keys to use for BM25 search instead of vector search
        weights (dict): The weights for the vector search
    Returns:
        list[dict]: The aggregation pipeline for the vector search
    '''
    link_to_keys = {rename_keys.get(key, key): v for key, v in attribs.items() if v is not None}
    weights = {rename_keys.get(key, key): value for key, value in weights.items()}
    filters = {}
    lexico_filters = []
    for key, val in attribs.items():
        if val is None or key in rename_keys or key in bm25_keys:
            continue
        filters[key] = _create_filter(val)
        lexico_filters.append(_create_filter(val, lexico_search_field=key))
    emb_attrs = {key: v for key, v in link_to_keys.items() if key.startswith('embedding') and v is not None}
    bm25_attribs = {k: v for k, v in attribs.items() if k in bm25_keys and v is not None}

    pipelines = {}
    flat_weights = {}

    for key, val in bm25_attribs.items():
        if filters:
            search_stage = {
                'index': 'bm25_index',
                'compound': {
                    'should': [
                        {'text': {'query': [val], 'path': key}},

                    ],
                **({'filter': lexico_filters} if lexico_filters else {})
                }
            }
        else:
            search_stage = {
                    'index': 'bm25_index',
                    'text': {'query': [val], 'path': key}
            }

        pipelines[key] = [{'$search': search_stage}]
        flat_weights[key] = weights.get(key, 1.0)


    for key, val in emb_attrs.items():
        pipelines[key] = [{'$vectorSearch': {
                    'index': 'vector_index',
                    'path': key,
                    'queryVector': embeddings.embed_query(val),
                    'numCandidates': max(150, min(k * 15, 10000)),
                    'limit': k*5, # overfetch
                    **({'filter': filters} if filters else {})
                }
        }]
        flat_weights[key] = weights.get(key, 1.0)

    # need pipelines with reciprocal rank fusion
    return [{
        '$rankFusion': {
            'input': {'pipelines': pipelines},
            'combination': {'weights': flat_weights}
        }
    }, {'$limit': k}]


# NOTE: leaving out deadline
@dataclass(frozen=True)
class Exam:
    data: dict
    infocard: str = field(init=False)

    def __post_init__(self):
        default = 'Unbekannt'
        object.__setattr__(self, 'infocard', f'''Name: {self.data.get('name')};
Klausur-ID: {self.data.get('id')};
MongoDB-ID: {self.data.get('_id')};
Beschreibung: {self.data.get('description', default)};
Klausurart: {self.data.get('type')};
Dauer: {self.data.get('duration', default)};
Benotet: {self.data.get('graded')};
Vorbereitung: {self.data.get('preparation', default)};
Notenanteil an Modul: {self.data.get('portion_of_grade', default)};
Turnus: {self.data.get('frequency', default)}''')

    def __str__(self) -> str:
        return self.infocard


@dataclass(frozen=True)
class Module:
    data: dict
    infocard: str = field(init=False)

    def __post_init__(self):
        default = 'Unbekannt'
        semester_span = self.data.get('recommended_semester_span', default) or default
        if not isinstance(semester_span, str):
            start = semester_span.get('start_semester')
            if start == 99: start = 'Freie Wahl'
            end = semester_span.get('end_semester')
            if end == 99: end = 'Freie Wahl'
            semester_span = f"{start} - {end}"
        available_semesters = self.data.get('available_semesters', default)
        if not isinstance(available_semesters, str):
            available_semesters = 'start: ' + (available_semesters['start_semester'] or default) + ', end: ' + (available_semesters['end_semester'] or 'Unbeschränkt') + ', frequency: ' + (available_semesters['frequency'] or default)
        workloads = self.data.get('workloads', default) or default
        if not isinstance(workloads, str):
            workloads = ',\n'.join([f'    name: {wl["name"]}\n    in presence: {wl["in_presence"]}\n    time expenditure in hours: {wl["time_expenditure"]}' for wl in workloads])
        exams = self.data.get('exams', default)
        if not isinstance(exams, str):
            exams = '\n' + '\n'.join(['\t--- Klausurblock ---\n\t' + ',\n\t'.join(Exam(i).infocard.split(';\n')) for i in exams])

        object.__setattr__(self, 'infocard', f'''Name: {self.data.get('name')}
Modulcode: {self.data.get('module_code')}
MongoDB-ID: {self.data.get('_id')}
ECTS: {self.data.get('ects')}
Lehrstuhl: {self.data.get('faculty_chair')}
Verpflichtend: {self.data.get('mandatory')}
Wochenarbeitsstunden: {self.data.get('weekly_hours', default) or default}
Voraussetzungen: {self.data.get('prerequisites', default) or default}
Bestehensvoraussetzungen: {self.data.get('success_requirements', default) or default}
Empfohlener Absolvierungszeitraum von bis Semester: {semester_span}
Dauer in Semestern: {self.data.get('semester_span', default) or default}
<Inhalt>: <{self.data.get('content', default) or default}>
<Ziele>: <{self.data.get('goals', default) or default}>
Dozent: {self.data.get('lecturer', default) or default}
Sprachen: {', '.join(self.data.get('languages', [])) if self.data.get('languages') else default}
International: {self.data.get('international')}
Angeboten in den Semestern: {available_semesters}
Wochenstunden: {self.data.get('weekly_hours', default) or default}
Workload-Stunden: {self.data.get('workload_hours', default) or default}
Workloads: {workloads}
Lehrstuhl: {self.data.get('faculty_chair', default) or default}
Klausurbeschreibung: {self.data.get('exam_outline', default) or default}
Prüfungen: {exams}''')
        # Prüfungen (MongoDB-IDs): {', '.join(map(str, self.data.get('exams', []))) if self.data.get('exams') else default}''')

    def __str__(self) -> str:
        return self.infocard


@dataclass(frozen=True)
class ModuleHandbook:
    data: dict
    granularities: list[Literal['all', 'compressed', 'ids']] = field(default_factory=lambda: ['all', 'compressed', 'ids'])
    infocard: str = field(init=False)
    infocard_compressed_modules: str = field(init=False)
    infocard_module_ids_only: str = field(init=False)

    def __post_init__(self):
        default = 'Unbekannt'
        start_semester = self.data.get('start_semester')
        module_groups = module_groups_compressed = module_groups_ids = self.data.get('module_groups', default) or default

        def _create_infocard(mdl_grp: str) -> str:
            '''
            Creates an infocard string for the module handbook with the specified module group information.

            Args:
                mdl_grp (str): The module group information to include in the infocard.
            Returns:
                str: A string representation of the infocard for the module handbook.
            '''
            return f'''Name: {self.data.get('name')};
            MongoDB-ID: {self.data.get('_id')};
            Beginn: {start_semester};
            Fakultäten: {', '.join(self.data.get('faculties'))};
            Modulhandbuchgruppe: {self.data.get('module_handbook_group', default)};
            Dateipfad: {self.data.get('path').split('uni-a_mhbs_json', 1)[1][1:]}; # NOTE: replace hardcoded path
            Gründung des Studiengangs: {self.data.get('description', default)};
            Modulgruppen: {mdl_grp}''' # type: ignore

        def _create_module_group(module_group: dict, information: Literal['all', 'compressed', 'ids']) -> str:
            '''
            Creates a string representation of a module group with the specified information granularity.

            Args:
                module_group (dict): The module group data.
                information (Literal['all', 'compressed', 'ids']): The level of detail to include in the output. 'all' includes full module details, 'compressed' includes name and module code, and 'ids' includes only MongoDB IDs.
            Returns:
                str: A string representation of the module group with the specified information granularity.
            '''
            modules = module_group.get('modules', default)
            if modules is None:
                modules = default
            if not isinstance(modules, str):
                if information == 'ids':
                    modules = ', '.join([str(i.get('_id', default)) for i in modules])
                elif information == 'compressed':
                    modules = ', '.join([f'<{i.get("name")}, {i.get("module_code")}, {i.get("_id")}>' for i in modules])
                else:
                    modules = '\n'.join(['        --- Modul ---\n' + '\n        '.join(Module(i).infocard.split(';\n')) for i in modules])
            return f'''\tName: {module_group.get('name_letter')},
\tZu absolvierende ECTS: {module_group.get('min_ects', default) or default} - {module_group.get('max_ects', default) or default},
\tModule {" (MongoDB-IDs)" if information == 'ids' else "<Name, Modulcode, MongoDB-ID>" if information == 'compressed' else ""}: {modules}'''

        if not isinstance(module_groups, str):
            if 'compressed' in self.granularities:
                module_groups_compressed = '\n' + '\n'.join(['    --- Modulgruppe ---\n' + _create_module_group(i, information='compressed') for i in module_groups])
                object.__setattr__(self, 'infocard_compressed_modules', _create_infocard(mdl_grp=module_groups_compressed))
            if 'ids' in self.granularities:
                module_groups_ids = '\n' + '\n'.join(['    --- Modulgruppe ---\n' + _create_module_group(i, information='ids') for i in module_groups])
                object.__setattr__(self, 'infocard_module_ids_only', _create_infocard(mdl_grp=module_groups_ids))
            if 'all' in self.granularities:
                module_groups = '\n' + '\n'.join(['    --- Modulgruppe ---\n' + _create_module_group(i, information='all') for i in module_groups])
                object.__setattr__(self, 'infocard', _create_infocard(mdl_grp=module_groups))
        if start_semester is not None:
            start_semester = str(start_semester)
            is_winter_start = bool(start_semester[-1])
            year = start_semester[:4]
            start_semester = ('Wintersemester ' if is_winter_start else 'Sommersemester ') + str(year) + (f'/{int(year) + 1}' if is_winter_start else '')

    def __str__(self) -> str:
        return self.infocard


# NOTE: search_field Literal options originate from embedding_ fields in mongo_db/create_collection.py
@tool
async def get_studiengang_modulhandbuch(
    # module_handbook: str | None = None,
    name: str | None = None,
    description: str | None = None,
    faculties: str | None = None,
    path: str | None = None,
    start_semester: int | tuple[int | None, int | None] | None = None,
    k: int = 5) -> str | ValueError:
    '''
    Gibt passende Modulhandbücher von Studiengängen zurück.
    Verwende mindestens einen semantischen Parameter (module_handbook, name, description, faculties, path).

    Args:
        name (str | None): Der Name des Modulhandbuchs, nach dem gesucht werden soll (SEMANTISCHE SUCHE).
        description (str | None): Ab wann man den  Studiengang studieren kann (SEMANTISCHE SUCHE).
        faculties (str | None): Die Fakultäten des Studiengangs, nach denen gesucht werden soll (SEMANTISCHE SUCHE).
        path (str | None): Der Pfad des Modulhandbuchs, nach dem gesucht werden soll (SEMANTISCHE SUCHE).
        start_semester (int | tuple[int | None, int | None] | None): Der Startsemester des Modulhandbuchs, nach dem gesucht werden soll (FILTER). Eine einzelnze Zahl bedeutet ein genaues Match, ein Tuple bedeutet (min, max), wobei auch ein Wert auf None gesetzt werden kann, um nur min oder nur max zu spezifizieren.
        k (int): Die Anzahl der zurückzugebenden relevanten Ergebnisse.

    Returns:
        str | ValueError: Eine Liste von Modulhandbüchern (Studiengängen). ValueError, wenn keine semantischen Parameter angegeben wurden.
    '''
    # module_handbook (str | None): Suche mit einem gesamten Modulhandbuchobjekt, das durch infocard() umgewandelt wurde und bei dem alle Unbekannt-Werte danach entfernt wurden (SEMANTISCHE SUCHE).
    attribs = locals()
    attribs.pop('k')
    # rename_keys = {'module_handbook': 'embedding'}
    rename_keys = {k: v for k, v in zip(embedded_keys['mhbs'], embedded_keys_paths['mhbs'])} | {'module_handbook': 'embedding'}
    # bm25 = ['name', 'description', 'faculties', 'path']
    bm25 = bm25_keys['mhbs']
    for i in bm25:
        rename_keys.pop(i, None)
    if not any(attribs.get(key) is not None for key in (rename_keys.keys() | bm25)):
        raise ValueError('At least one of name, description or faculties must be provided for semantic or lexicographic search.')
    # NOTE: hardcode weights to make it easier for model as this is set manually and shall not be influenced by the model
    # TODO: refine weights
    weights = {'module_handbook': 1.0, 'name': 1.0, 'description': 0.5, 'faculties': 0.6, 'path': 0.8}
    # NOTE: check manual implementation: each embedding field must have a weight
    if set(rename_keys.keys()).union(set(bm25)) != set(weights.keys()): # use sets for avoiding order
        raise ValueError(f'Weights must be specified for all embedding fields. Missing weights for: {set(rename_keys.keys()) - set(weights.keys())}')
    lookup_modules = [ '_id', 'module_code', 'name']
    lookup_pipeline = [
        {'$lookup': {
                'from': 'modules',
                'localField': 'module_groups.modules',
                'foreignField': '_id',
                'as': '_modules',
                'pipeline': [
                    {'$project': {k: 1 for k in lookup_modules}}
                ]
            }
        },
        {'$set': {
            'module_groups': {
                '$map': {
                    'input': '$module_groups',
                    'as': 'mg',
                    'in': {'$mergeObjects': [
                        '$$mg', {
                            'modules': {
                                '$map': {
                                    'input': '$$mg.modules',
                                    'as': 'm',
                                    'in': {
                                        '$first': {'$filter': {
                                            'input': '$_modules',
                                            'as': 'mods',
                                            'cond': {'$eq': ['$$mods._id', '$$m']}
                                        }}
                                    }
                                }
                            }
                        }
                    ]}
                }
            }}
        },
        {'$unset': '_modules'}
    ]
    agg_pipeline = _create_vector_search(attribs=attribs, rename_keys=rename_keys, bm25_keys=bm25, weights=weights, k=k)
    agg_pipeline.extend(lookup_pipeline)
    cursor = mhbs_db.aggregate(agg_pipeline)
    results = cursor.to_list(length=k)
    outputs = [ModuleHandbook(i, granularities=['compressed']).infocard_compressed_modules for i in results]
    return '\n\n--- Neues Suchresultat ---\n\n'.join(outputs)


# TODO: add filters either in new function or in get_studiengang_modulhandbuch
@tool
async def get_modul(
    # module: str | None = None,
    name: str | None = None,
    content: str | None = None,
    goals: str | None = None,
    lecturer: str | None = None,
    prerequisites: str | None = None,
    faculty_chair: str | None = None,
    workloads: str | None = None,
    success_requirements: str | None = None,
    exam_outline: str | None = None,
    mandatory: bool | None = None,
    module_code: str | None = None,
    ects: int | tuple[int | None, int | None] | None = None,
    available_semesters: int | tuple[int | None, int | None] | None = None,
    recommended_semester_span: int | tuple[int | None, int | None] | None = None,
    languages: list[Literal['Deutsch', 'Englisch', 'alle Sprachen', 'Französisch', 'Spanisch', 'Japanisch', 'Italienisch', 'Portugiesisch', 'Rumänisch', 'Arabisch', 'Chinesisch', 'Schwedisch', 'Türkisch', 'Russisch']] | None = None,
    international: bool | None = None,
    weekly_hours: int | tuple[int | None, int | None] | None = None,
    workload_hours: int | tuple[int | None, int | None] | None = None,
    exams: list[int] | None = None,
    k: int = 5) -> str | ValueError:
    '''
    Gibt Informationen zu passenden Modulen zurück.if not any(attribs.get(key) is not None for key in (rename_keys.keys() | bm25)):
            raise ValueError('At least one of name, content, goals, lecturer, prerequisites, faculty_chair, workloads, success_requirements or exam_outline must be provided for semantic or lexicographic search.')
    Verwende mindestens einen semantischen Parameter (module, name, content, goals, lecturer, prerequisites, faculty_chair, workloads, success_requirements, exam_outline).
exam, name, description, preparation, type, duration, or frequency
    Args:
        name (str | None): Der Name des Moduls, nach dem gesucht werden soll (SEMANTISCHE SUCHE).
        content (str | None): Der Inhalt des Moduls, nach dem gesucht werden soll (SEMANTISCHE SUCHE).
        goals (str | None): Die Ziele des Moduls, nach denen gesucht werden soll (SEMANTISCHE SUCHE).
        lecturer (str | None): Der Dozent des Moduls, nach dem gesucht werden soll (SEMANTISCHE SUCHE).
        prerequisites (str | None): Die Voraussetzungen des Moduls, nach denen gesucht werden soll (SEMANTISCHE SUCHE).
        faculty_chair (str | None): Der Lehrstuhl des Moduls, nach dem gesucht werden soll (SEMANTISCHE SUCHE).
        workloads (str | None): Die Arbeitsbelastung des Moduls, nach der gesucht werden soll, das durch infocard() umgewandelt wurde und bei dem alle Unbekannt-Werte entfernt wurden (SEMANTISCHE SUCHE).
        success_requirements (str | None): Die Erfolgsvoraussetzungen des Moduls, nach denen gesucht werden soll (SEMANTISCHE SUCHE).
        exam_outline (str | None): Die Prüfungsordnung des Moduls, nach der gesucht werden soll (SEMANTISCHE SUCHE).
        mandatory (bool | None): Ob das Modul verpflichtend ist, nach dem gesucht werden soll (FILTER).
        module_code (str | None): Der Modulcode des Moduls, nach dem gesucht werden soll (FILTER). Es können auch Teil-codes angegeben werden, um beispielsweise nur nach der Fakultät zu suchen.
        ects (int | tuple[int | None, int | None] | None): Die ECTS-Punkte des Moduls, nach denen gesucht werden soll (FILTER). Eine einzelnze Zahl bedeutet ein genaues Match, ein Tuple bedeutet (min, max), wobei auch ein Wert auf None gesetzt werden kann, um nur min oder nur max zu spezifizieren.
        available_semesters (int | tuple[int | None, int | None] | None): Die verfügbaren Semester des Moduls, nach denen gesucht werden soll (FILTER). Eine einzelnze Zahl bedeutet ein genaues Match, ein Tuple bedeutet (min, max), wobei auch ein Wert auf None gesetzt werden kann, um nur min oder nur max zu spezifizieren.
        recommended_semester_span (int | tuple[int | None, int | None): Die empfohlene Semesteranzahl des Moduls, nach der gesucht werden soll (FILTER). Eine einzelnze Zahl bedeutet ein genaues Match, ein Tuple bedeutet (min, max), wobei auch ein Wert auf None gesetzt werden kann, um nur min oder nur max zu spezifizieren.
        languages (list[Literal['Deutsch', 'Englisch', 'alle Sprachen', 'Französisch', 'Spanisch', 'Japanisch', 'Italienisch', 'Portugiesisch', 'Rumänisch', 'Arabisch', 'Chinesisch', 'Schwedisch', 'Türkisch', 'Russisch']] | None): Die Sprachen des Moduls, nach denen gesucht werden soll (FILTER). Eine Liste von Sprachen, die im Modul enthalten sein müssen.
        international (bool | None): Ob das Modul international ist, nach dem gesucht werden soll (FILTER).
        weekly_hours (int | tuple[int | None, int | None] | None): Die wöchentlichen Stunden des Moduls, nach denen gesucht werden soll (FILTER). Eine einzelnze Zahl bedeutet ein genaues Match, ein Tuple bedeutet (min, max), wobei auch ein Wert auf None gesetzt werden kann, um nur min oder nur max zu spezifizieren.
        workload_hours (int | tuple[int | None, int | None] | None): Die Arbeitsstunden des Moduls, nach denen gesucht werden soll (FILTER). Eine einzelnze Zahl bedeutet ein genaues Match, ein Tuple bedeutet (min, max), wobei auch ein Wert auf None gesetzt werden kann, um nur min oder nur max zu spezifizieren.
        exams (list[int] | None): Die Prüfungen des Moduls, nach denen gesucht werden soll (FILTER). Eine Liste von Prüfungs-IDs, die im Modul enthalten sein müssen.
        k (int): Die Anzahl der zurückzugebenden relevanten Ergebnisse.
    Returns:
        str | ValueError: Informationen zu passenden Modulen. ValueError, wenn keine semantischen Parameter angegeben wurden.
    '''
    # module (str | None): Suche mit einem gesamten Modulobjekt, das durch infocard() umgewandelt wurde und bei dem alle Unbekannt-Werte danach entfernt wurden (SEMANTISCHE SUCHE).
    # TODO: change Fakultät in docstring for mandatory
    attribs = locals()
    attribs.pop('k')
    # rename_keys = {'module': 'embedding', 'content': 'embedding_content', 'goals': 'embedding_goals', 'workloads': 'embedding_workloads', 'exam_outline': 'embedding_exam_outline'}
    rename_keys = {k: v for k, v in zip(embedded_keys['modules'], embedded_keys_paths['modules'])} | {'module': 'embedding'}
    # bm25 = ['name', 'lecturer', 'prerequisites', 'faculty_chair', 'success_requirements']
    bm25 = bm25_keys['modules']
    for i in bm25:
        rename_keys.pop(i, None)
    if not any(attribs.get(key) is not None for key in (rename_keys.keys() | bm25)):
        raise ValueError('At least one of name, content, goals, lecturer, prerequisites, faculty_chair, workloads, success_requirements or exam_outline must be provided for semantic or lexicographic search.')
    weights = {'module': 1.0, 'name': 1.0, 'content': 1.0, 'goals': 1.0, 'lecturer': 0.6, 'prerequisites': 0.8, 'faculty_chair': 1.0, 'workloads': 0.8, 'success_requirements': 0.6, 'exam_outline': 0.6}
    # NOTE: check manual implementation: each embedding field must have a weight
    if set(rename_keys.keys()).union(set(bm25)) != set(weights.keys()): # use sets for avoiding order
        raise ValueError(f'Weights must be specified for all embedding fields. Missing weights for: {set(rename_keys.keys()) - set(weights.keys())}')
    agg_pipeline = _create_vector_search(attribs=attribs, rename_keys=rename_keys, bm25_keys=bm25, weights=weights, k=k)
    agg_pipeline.append(
        {'$lookup': {
            'from': 'exams',
            'foreignField': '_id',
            'localField': 'exams',
            'as': 'exams'
        }}
    )
    cursor = modules_db.aggregate(agg_pipeline)
    results = cursor.to_list(length=k)
    outputs = [Module(i).infocard for i in results]
    return '\n\n--- Neues Suchresultat ---\n\n'.join(outputs)


# NOTE: use at least one semantic parameter so ranking is possible when limiting the output to k results
@tool
async def get_klausur(
    # exam: str | None = None,
    name: str | None = None,
    description: str | None = None,
    preparation: str | None = None,
    type: str | None = None,
    duration: str | None = None,
    frequency: str | None = None,
    deadline: int | tuple[int | None, int | None] | None = None,
    graded: bool | None = None,
    id: int | None = None,
    portion_of_grade: int | tuple[int | None, int | None] | None = None,
    k: int = 5) -> str | ValueError:
    '''
    Gibt Informationen zu passenden Klausuren zurück.
    Verwende mindestens einen semantischen Parameter (exam, name, description, preparation, type, duration, frequency).

    Args:
        name (str | None): Der Name der Klausur, nach dem gesucht werden soll (SEMANTISCHE SUCHE).
        description (str | None): Die Beschreibung der Klausur, nach der gesucht werden soll (SEMANTISCHE SUCHE).
        preparation (str | None): Die Vorbereitung auf die Klausur, nach der gesucht werden soll (SEMANTISCHE SUCHE).
        type (str | None): Der Typ der Klausur, nach dem gesucht werden soll (SEMANTISCHE SUCHE).
        duration (str | None): Die Dauer der Klausur, nach der gesucht werden soll (SEMANTISCHE SUCHE).
        frequency (str | None): Die Häufigkeit der Klausur, nach der gesucht werden soll (SEMANTISCHE SUCHE).
        deadline (int | tuple[int | None, int | None] | None): Die Deadline der Klausur, nach der gesucht werden soll (FILTER). Eine einzelnze Zahl bedeutet ein genaues Match, ein Tuple bedeutet (min, max), wobei auch ein Wert auf None gesetzt werden kann, um nur min oder nur max zu spezifizieren.
        graded (bool | None): Ob die Klausur benotet ist, nach dem gesucht werden soll (FILTER).
        id (int | None): Die ID der Klausur, nach der gesucht werden soll (FILTER).
        portion_of_grade (int | tuple[int | None, int | None] | None): Der Anteil an der Note der Klausur, nach dem gesucht werden soll (FILTER). Eine einzelnze Zahl bedeutet ein genaues Match, ein Tuple bedeutet (min, max), wobei auch ein Wert auf None gesetzt werden kann, um nur min oder nur max zu spezifizieren.
        k (int): Die Anzahl der zurückzugebenden relevanten Ergebnisse.
    Returns:
        str | ValueError: Informationen zu passenden Klausuren. ValueError, wenn keine semantischen Parameter angegeben wurden.
    '''
    # exam (str | None): Suche mit einem gesamten Klausurobjekt, das durch infocard() umgewandelt wurde und bei dem alle Unbekannt-Werte danach entfernt wurden (SEMANTISCHE SUCHE).
    attribs = locals()
    attribs.pop('k')
    # bm25 = ['name', 'type', 'duration', 'frequency']
    bm25 = bm25_keys['exams']
    rename_keys = {k: v for k, v in zip(embedded_keys['exams'], embedded_keys_paths['exams'])} | {'exam': 'embedding'}
    # rename_keys = {'exam': 'embedding', 'name': 'embedding_name', 'description': 'embedding_description', 'preparation': 'embedding_preparation', 'type': 'embedding_type', 'duration': 'embedding_duration', 'frequency': 'embedding_frequency'}
    for i in bm25:
        rename_keys.pop(i, None)
    if not any(attribs.get(key) is not None for key in (rename_keys.keys() | bm25)):
        raise ValueError('At least one of exam, name, description, preparation, type, duration, or frequency must be provided for semantic or lexicographic search.')
    # NOTE: hardcode weights to make it easier for model as this is set manually and shall not be influenced by the model
    # TODO: refine weights
    weights = {'exam': 1.0, 'name': 1.0, 'description': 1.0, 'preparation': 0.8, 'type': 0.7, 'duration': 0.6, 'frequency': 0.5}

    # NOTE: check manual implementation: each embedding field must have a weight
    if set(rename_keys.keys()).union(set(bm25)) != set(weights.keys()): # use sets for avoiding order
        raise ValueError(f'Weights must be specified for all embedding fields. Missing weights for: {set(rename_keys.keys()) - set(weights.keys())}')

    agg_pipeline = _create_vector_search(attribs=attribs, rename_keys=rename_keys, bm25_keys=bm25, weights=weights, k=k)
    cursor = exams_db.aggregate(agg_pipeline)
    results = cursor.to_list(length=k)
    outputs = [Exam(i).infocard for i in results]
    return '\n\n--- Neues Suchresultat ---\n\n'.join(outputs)


@tool
def get_klausur_by_mongodb_id(mongo_id: str) -> str | None:
    '''
    Gibt Informationen zu einer Klausur anhand der MongoDB-ID zurück.

    Args:
        mongo_id (str): Die MongoDB-ID der Klausur, nach der gesucht werden soll.
    Returns:
        str | None: Informationen zu der Klausur. None, wenn keine Klausur mit der angegebenen MongoDB-ID gefunden wurde.
    '''
    result = exams_db.find_one({'_id': ObjectId(mongo_id)})
    if result:
        return Exam(result).infocard
    return None

@tool
def get_modul_by_mongodb_id(mongo_id: str) -> str | None:
    '''
    Gibt Informationen zu einem Modul anhand der MongoDB-ID zurück.

    Args:
        mongo_id (str): Die MongoDB-ID des Moduls, nach der gesucht werden soll.
    Returns:
        str | None: Informationen zu dem Modul. None, wenn kein Modul mit der angegebenen MongoDB-ID gefunden wurde.
    '''
    result = modules_db.find_one({'_id': ObjectId(mongo_id)})
    if result:
        return Module(result).infocard
    return None

@tool
def get_modulhandbuch_by_mongodb_id(mongo_id: str) -> str | None:
    '''
    Gibt Informationen zu einem Modulhandbuch anhand der MongoDB-ID zurück.

    Args:
        mongo_id (str): Die MongoDB-ID des Modulhandbuchs, nach der gesucht werden soll.
    Returns:
        str | None: Ausführliche Informationen zu dem Modulhandbuch. None, wenn kein Modulhandbuch mit der angegebenen MongoDB-ID gefunden wurde.
    '''
    result = mhbs_db.find_one({'_id': ObjectId(mongo_id)})
    if result:
        return ModuleHandbook(result).infocard # _compressed_modules
    return None


def replacer(match):
    label, url = match.group(1), match.group(2)
    absolute = urljoin('https://www.uni-augsburg.de', url)
    return f'URL to {label}: {absolute}'


# TODO: use search engine to search for query then only allow uni augsburg links in the found urls or specify site: but that changes results to the worse
"""@DeprecationWarning
@tool
async def suche_uni_augsburg_website(url: str = 'https://www.uni-augsburg.de') -> str:
    '''
    Durchsucht die Website der Universität Augsburg nach Informationen zu Studiengängen, Modulen und Klausuren.

    Args:
        url (str): Die URL der Website, die durchsucht werden soll.
    Returns:
        str: Die gefundenen Informationen von der Website. Wenn keine Informationen gefunden werden, wird eine entsprechende Nachricht zurückgegeben oder ein Fehlerstring.
    '''
    if not re.match(r'^https://www\.([a-zA-Z0-9-]+\.)?uni-augsburg\.de(/.*)?$', url):
        return 'Fehler: Ungültige URL. Bitte gib eine URL von der Universität Augsburg an. Diese muss mit "https://www.uni-augsburg.de" beginnen.'

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; MyAgent/1.0)'
            })
            response.raise_for_status()
    except httpx.HTTPError as e:
        return f'Failed to fetch {url}: {e}'

    text = trafilatura.extract(response.text, include_links=True)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replacer, text)
    if not text:
        return f'Es konnte kein Text von {url} extrahiert werden.'

    return text"""


# TODO: maybe rather use BERT extractive summarization for performance
async def _condense_text(text: str, query: str) -> str:
    '''
    Condenses the text to focus on information relevant to the query.

    Args:
        text (str): The text to be condensed.
        query (str): The query to focus on.
    Returns:
        str: The condensed text.
    '''
    prompt = f'''Fasse den folgenden Text zusammen, mit Fokus auf Informationen,
    die für diese Frage relevant sind: '{query}'
    Lass irrelevante Inhalte (Navigation, Kontaktdaten, Impressum etc.) weg.
    Fasse nur lange Texte zusammen, der Output sollte immer noch alle Informationen mit Relevanz beinhalten.'''
    user_query = text

    async with httpx.AsyncClient(base_url='http://localhost:11434', timeout=30, follow_redirects=False) as condense_client:
        response = await condense_client.post(
                '/api/chat',
                json={
                    'model': mdl,
                    'messages': [{'role': 'system', 'content': prompt}, {'role': 'user', 'content': user_query}],
                    'stream': False,
                    'options': {'num_predict': 300, 'temperature': 0.3},
                },
            )
        response.raise_for_status()
        data = response.json()
        summary = data['message']['content']
    return summary



@tool
async def dirty_search(query: str, k: int = 3) -> str:
    '''
    Findet Seiten der Uni Augsburg mit Informationen zu dem Query.
    Verwende diese Suche nur als Fallback, wenn search_intranet nichts findet.
    Diese Suche greift nur auf den öffentlichen Teil der Website zu, funktioniert aber besonders gut, wenn Tippfehler in der Suchanfrage vorhanden sind.

    Args:
        query (str): Die Suchanfrage, die Informationen oder eine Frage enthält. Mache deutlich, dass sich das Query auf die Universität Augsburg bezieht.
        k (int): Die Anzahl der zurückzugebenden relevanten Ergebnisse. Empfohlen sind 5 bis 7, da die Rückgabe sonst sehr lang werden kann.
    Returns:
        str: Die relevantesten Informationen von der Website der Universität Augsburg, die der Anfrage entsprechen. Wenn keine relevanten Informationen gefunden werden, wird eine entsprechende Nachricht zurückgegeben. Suchresultate werden durch '\n\n---\n\n' getrennt.
    '''
    res = []
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
            res = await client.get(
                'http://localhost:8888/search?q=',
                params={'q': f'site:uni-augsburg.de {query}', 'format': 'json'},
                headers={
                    "Accept": "application/json",
                }
            )
            res.raise_for_status()
    except httpx.HTTPError:
        return "Fehler bei der Suche"
    # TODO: load additional pages when results smaller than k
    res = [{k: v for k, v in i.items() if k in ['title', 'content', 'url']} for i in res.json().get('results', [])][:k]
    res = [r['url'] for r in res if re.match(r'^https://www\.([a-zA-Z0-9-]+\.)?uni-augsburg\.de(/.*)?$', r['url'])]
    if not res:
        return 'Keine passenden Informationen gefunden.'
    results = []
    for url in res:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; MyAgent/1.0)"
                })
                response.raise_for_status()
        except httpx.HTTPError:
            continue

        if response.url != url and response.url:
            url = str(response.url)
        text = htm.convert(response.text, options=options).content
        print(text)
        if not text:
            continue
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replacer, text)
        # text = text.replace('@uni-auni-a.de', '@uni-a.de')
        splitted = text.split('@')
        for i in range(1, len(splitted)):
            email_end, rest = splitted[i].split('.de', 1)
            # unia website always marks email domains thick so remove the non thick part (has to match the thick part)
            if len(email_end) > 3 and len(email_end) < 50 and (split := email_end.split('**', 3))[0] == split[1]:
                email_end = f'@{email_end.split('**', 3)[1]}.de'
            else:
                email_end = f'@{email_end}.de'
            splitted[i] = email_end + rest
        text = ''.join(splitted)
        # condensed_text = await _condense_text(text, query)
        results.append(f'Quelle: {url}\n{text}')
    if not results:
        return 'Keine passenden Informationen gefunden.'
    return '\n\n---\n\n'.join(results)
