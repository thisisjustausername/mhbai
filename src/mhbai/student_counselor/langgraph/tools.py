'''
Create tools for searching and retrieving information about study programs, modules, and exams from the internal information cards of the University of Augsburg.
'''

# TODO: don't make get studiengang etc output the full information but rather only like a short infocard to keep context small. then for more infos either activate full info or fetch by id one by one or concurrently

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

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

mhb_lookup_modules = [ '_id', 'module_code', 'name']
mhb_lookup_pipeline = [
    {'$lookup': {
            'from': 'modules',
            'localField': 'module_groups.modules',
            'foreignField': '_id',
            'as': '_modules',
            'pipeline': [
                {'$project': {k: 1 for k in mhb_lookup_modules}}
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

module_lookup =  {'$lookup': {
    'from': 'exams',
    'foreignField': '_id',
    'localField': 'exams',
    'as': 'exams'
}}

################################################################
'''
Create tools
'''
################################################################

@tool
async def search_studiengang(query: str, k: int = 5) -> str:
    '''
    Durchsucht die internen Informationskarten für Studiengängen nach Studiengangsinformationen, Inhalten, Zulassungsvoraussetzungen (NC) und weiteren studiengangsspezifischen Fragen.
    Du kannst immer nur nach EINEM Studiengang pro Anfrage suchen. Für mehrere Studiengänge stelle mehrere Anfragen. Stelle die Anfragen NACHEINANDER, sonst treten Fehler auf. Nur unterschiedliche Studiengänge dürfen parallel gesucht werden. Sende sonst immer nur eine Suchanfrage und warte auf die Antwort bevor du die nächste Anfrage sendest.
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
    STRATEGIE:
    - Bei groben Fragen zu Themenbereichen und Berufsperspektiven
    - Schnell und günstig für Übersicht
    EINSATZGEBIET:
    - Studiengang-Namen
    - Inhalte
    - Berufsperspektiven
    - Ziele
    - Regelstudienzeit
    - Teil-/Vollzeitstudium
    - Zulassungsmodus
    - Studienbeginn
    - Unterrichtssprache
    - Gefordertes Deutschniveau
    IMMER enthaltene Felder:
      - Studiengangsname
      - Inhalt
      - Berufsperspektiven
      - Ziele
      - Regelstudienzeit
      - Teil-/Vollzeitstudium
      - Zulassungsmodus
      - Studienbeginn
      - Unterrichtssprache
      - Gefordertes Deutschniveau
    HINWEISE:
    - IMMER nur EINEN Studiengang pro Anfrage suchen
    - Nur Anfragen zu verschiedenen Studiengängen dürfen parallel gestellt werden
    - Bei groben Fragen zuerst verwenden (günstig)

    Args:
        query (str): Die Suchanfrage, die Informationen zu einem Studiengang oder studiengangsbezogenen Fragen enthält.
        k (int): Die Anzahl der zurückzugebenden relevanten Ergebnisse.

    Returns:
        str: Die relevantesten Informationen aus den Informationskarten, die der Anfrage entsprechen. Wenn keine relevanten Informationen gefunden werden, wird eine entsprechende Nachricht zurückgegeben. Es sind IMMER Informationen zu Studiengangsname, Inhalt, Berufsperspektiven, Ziele, Regelstudienzeit, Teil- / Vollzeitstudium, Zulassungsmodus, Studienbeginn, Unterrichtssprache, gefordertes Deutschniveau enthalten.
    '''
    matches = db.similarity_search(query, k=k)

    if not matches:
        return 'Keine passenden Informationen gefunden.'
    return json.dumps(
        [{
            'ranking': index + 1,
            'studiengang': match.metadata.get('Studiengang', 'unbekannt'),
            'inhalt': match.page_content,
            'metadaten': match.metadata
        }
            for index, match in enumerate(matches)
        ]
    )


def _build_vector_search(index: str, embedding: list[float], k: int, filters: list[dict] | None):
    return {
        '$vectorSearch': {
            'queryVector': embedding,
            'path': index,
            'limit': k*15,
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
    bm25_attribs = {key: v for key, v in attribs.items() if key in bm25_keys and v is not None}

    pipelines = {}
    flat_weights = {}

    ''''should': [
        {'text': {'query': [val], 'path': key}},

    ],'''

    for key, val in bm25_attribs.items():
        if filters:
            search_stage = {
                'index': 'bm25_index',
                'compound': {
                    'must': [
                        {
                            'text': {
                                'query': val,
                                'path': key,
                                'matchCriteria': 'all',
                                'fuzzy': {'maxEdits': 2, 'prefixLength': 1}
                            }
                        }
                    ],
                **({'filter': lexico_filters} if lexico_filters else {})
                }
            }
        else:
            search_stage = {
                    'index': 'bm25_index',
                    # 'text': {'query': [val], 'path': key}
                    'text': {
                        'query': val,
                        'path': key,
                        'matchCriteria': 'all',
                        'fuzzy': {'maxEdits': 2, 'prefixLength': 1}
                    }
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
    # infocard_text: str = field(init=False)
    infocard: dict = field(init=False)
    compact: bool = field(default=True)


    def __post_init__(self):
        default = 'Unbekannt'
        """info = f'''Name: {self.data.get('name')};
Klausur-ID: {self.data.get('id')};
MongoDB-ID: {self.data.get('_id')};
Beschreibung: {self.data.get('description', default)};
Klausurart: {self.data.get('type')};
Dauer: {self.data.get('duration', default)};
Benotet: {self.data.get('graded')};
Vorbereitung: {self.data.get('preparation', default)};
Notenanteil an Modul: {self.data.get('portion_of_grade', default)};
Turnus: {self.data.get('frequency', default)}'''"""
        info_dict = {
            'name': self.data.get('name'),
            'id': self.data.get('id'),
            'mongo_id': str(self.data.get('_id')),
            'beschreibung': self.data.get('description', default),
            'klausurart': self.data.get('type'),
            'dauer': self.data.get('duration', default),
            'benotet': self.data.get('graded'),
            'vorbereitung': self.data.get('preparation', default),
            'notenanteil_an_modul': self.data.get('portion_of_grade', default),
            'turnus': self.data.get('frequency', default)
        }

        if self.compact is True:
            unknowns_json = []
            keys_to_pop = []
            for k, v in info_dict.items():
                if v == default:
                    keys_to_pop.append(k)
                    unknowns_json.append(k)
            for k in keys_to_pop:
                info_dict.pop(k)
            if unknowns_json:
                info_dict['unbekannt'] = unknowns_json
            # fields = [i for i in info.split('\n')]
            """unknowns = []
            knowns = []
            for f in fields:
                if f.endswith(default):
                    unknowns.append(f.split(':')[0])
                else: knowns.append(f)
            info = '\n'.join(knowns)
            if unknowns: info = info + f'\nUnbekannt: {", ".join(unknowns)}'"""

        # object.__setattr__(self, 'infocard_text', info)
        object.__setattr__(self, 'infocard', info_dict)

    """def __str__(self) -> str:
        return self.infocard_text"""


@dataclass(frozen=True)
class Module:
    data: dict
    # infocard_text: str = field(init=False)
    infocard: dict = field(init=False)
    compact: bool = field(default=True)

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
        exams_json = exams
        if not isinstance(exams, str):
            exams_json = [Exam(i).infocard for i in exams]
            # exams = '\n' + '\n'.join(['\t--- Klausurblock ---\n\t' + ',\n\t'.join(Exam(i).infocard_text.split(';\n')) for i in exams])

        """info = f'''Name: {self.data.get('name')}
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
Workload-Stunden: {self.data.get('workload_hours', default) or default}
Workloads: {workloads}
Klausurbeschreibung: {self.data.get('exam_outline', default) or default}
Prüfungen: {exams}'''"""
        info_dict = {
            'name': self.data.get('name'),
            'modulcode': self.data.get('module_code'),
            'mongoDB-ID': str(self.data.get('_id')),
            'ects': self.data.get('ects'),
            'lehrstuhl': self.data.get('faculty_chair'),
            'verpflichtend': self.data.get('mandatory'),
            'wochenarbeitsstunden': self.data.get('weekly_hours', default) or default,
            'voraussetzungen': self.data.get('prerequisites', default) or default,
            'bestehensvoraussetzungen': self.data.get('success_requirements', default) or default,
            'empfohlener Absolvierungszeitraum von bis Semester': semester_span,
            'dauer in Semestern': self.data.get('semester_span', default) or default,
            'inhalt': self.data.get('content', default) or default,
            'ziele': self.data.get('goals', default) or default,
            'dozent': self.data.get('lecturer', default) or default,
            'sprachen': ', '.join(self.data.get('languages', [])) if self.data.get('languages') else default,
            'international': self.data.get('international'),
            'angeboten_in_den_semestern': available_semesters,
            'workload_stunden': self.data.get('workload_hours', default) or default,
            'workloads': workloads,
            'klausurbeschreibung': self.data.get('exam_outline', default) or default,
            'prüfungen': exams_json,
        }

        if self.compact is True:
            # excluded_fields = ['<Inhalt>', '<Ziele>', 'Workloads', 'Klausurbeschreibung', 'Voraussetzungen', 'Bestehensvoraussetzungen', 'Dozent', 'International', 'Prüfungen']
            excluded_fields_json = ['inhalt', 'ziele', 'workloads', 'klausurbeschreibung', 'voraussetzungen', 'bestehensvoraussetzungen', 'dozent', 'international', 'prüfungen']
            unknowns_json = []
            keys_to_pop = []
            for k, v in info_dict.items():
                if k in excluded_fields_json:
                    keys_to_pop.append(k)
                    continue
                if v == default:
                    keys_to_pop.append(k)
                    unknowns_json.append(k)
            for k in keys_to_pop:
                info_dict.pop(k)
            if unknowns_json:
                info_dict['unbekannt'] = unknowns_json
            """fields = [i for i in info.split('\n') if not i in excluded_fields]
            unknowns = []
            knowns = []
            for f in fields:
                if f.endswith(default):
                    unknowns.append(f.split(':')[0])
                else: knowns.append(f)
            info = '\n'.join(knowns)
            if unknowns: info = info + f'\nUnbekannt: {", ".join(unknowns)}'"""

        # object.__setattr__(self, 'infocard_text', info)
        object.__setattr__(self, 'infocard', info_dict)

    """def __str__(self) -> str:
        return self.infocard_text"""


@dataclass(frozen=True)
class ModuleHandbook:
    data: dict
    granularities: list[Literal['all', 'compressed', 'ids']] = field(default_factory=lambda: ['all', 'compressed', 'ids'])
    infocard: dict = field(init=False)
    infocard_compressed_modules: tuple = field(init=False)
    infocard_module_ids_only: tuple = field(init=False)
    """infocard_text: str = field(init=False)
    infocard_compressed_modules_text: str = field(init=False)
    infocard_module_ids_only_text: str = field(init=False)"""
    compact: bool = field(default=True)

    def __post_init__(self):
        default = 'Unbekannt'
        start_semester = self.data.get('start_semester')
        module_groups = module_groups_compressed = module_groups_ids = self.data.get('module_groups', default) or default

        def _create_infocard(mdl_grp: str | tuple) -> dict:
            '''
            Creates an infocard dictionary for the module handbook with the specified module group information.

            Args:
                mdl_grp (str | tuple): The module group information to include in the infocard.
            Returns:
                dict: A dictionary representation of the infocard for the module handbook.
            '''
            # excluded_fields = ['Modulgruppen', 'Gründung des Studiengangs']
            excluded_fields_json = ['modulgruppen', 'gründung_des_studiengangs']
            """info = f'''Name: {self.data.get('name')}
MongoDB-ID: {self.data.get('_id')}
Beginn: {start_semester}
Fakultäten: {', '.join(self.data.get('faculties'))}
Modulhandbuchgruppe: {self.data.get('module_handbook_group', default)}
Dateipfad: {self.data.get('path').split('uni-a_mhbs_json', 1)[1][1:]}
Gründung des Studiengangs: {self.data.get('description', default)}
Modulgruppen: {mdl_grp if isinstance(mdl_grp, str) else ""}''' # temporary else empty fix"""
# TODO: above remove empty
            info_dict = {
                'name': self.data.get('name'),
                'mongoDB-ID': str(self.data.get('_id')),
                'beginn': start_semester,
                'fakultäten': self.data.get('faculties'),
                'modulhandbuchgruppe': self.data.get('module_handbook_group', default),
                'dateipfad': self.data.get('path').split('uni-a_mhbs_json', 1)[1][1:], # TODO: remove hardcoded path
                'gründung_des_studiengangs': self.data.get('description', default),
                'modulgruppen': mdl_grp
            }

            if self.compact is False:
                return info_dict
            unknowns_json = []
            keys_to_pop = []
            for k, v in info_dict.items():
                if k in excluded_fields_json:
                    keys_to_pop.append(k)
                    continue
                if v == default:
                    keys_to_pop.append(k)
                    unknowns_json.append(k)
            for k in keys_to_pop:
                info_dict.pop(k)
            if unknowns_json:
                info_dict['unbekannt'] = unknowns_json
            """if 'Modulgruppen' in excluded_fields:
                info = info.split('\nModulgruppen: ', 1)[0]"""
            # return '\n'.join([i for i in info.split('\n') if not i.split(':', 1)[0] in excluded_fields])
            return info_dict

        """@overload
        def _create_module_group(module_group: dict, information: Literal['all', 'compressed', 'ids'], output_format=Literal['dict']) -> dict: ...

        @overload
        def _create_module_group(module_group: dict, information: Literal['all', 'compressed', 'ids'], output_format=Literal['str']) -> str: ..."""

        def _create_module_group(module_group: dict, information: Literal['all', 'compressed', 'ids']) -> dict:
            '''
            Creates a string or dictionary representation of a module group with the specified information granularity.

            Args:
                module_group (dict): The module group data.
                information (Literal['all', 'compressed', 'ids']): The level of detail to include in the output. 'all' includes full module details, 'compressed' includes name and module code, and 'ids' includes only MongoDB IDs.
            Returns:
                dict: A dictionary representation of the module group with the specified information granularity.
            '''
            modules = module_group.get('modules', default)
            modules_json = modules
            if modules is None:
                modules = default
                modules_json = default
            if not isinstance(modules, str):
                if information == 'ids':
                    # modules = ', '.join([str(i.get('_id', default) if isinstance(i, dict) else i) for i in modules]) # TODO: test isinstance
                    # either dictionary or when no match found the object id
                    modules_json = [str(i.get('_id', default) if isinstance(i, dict) else i) for i in modules]
                elif information == 'compressed':
                    # modules = ', '.join([f'<{i.get("name")}, {i.get("module_code")}, {i.get("_id")}>' if isinstance(i, dict) else f'<{default}, {default}, {i}' for i in modules])
                    modules_json = [{'name': i.get('name'), 'modulcode': i.get('module_code'), 'mongoDB-ID': i.get('_id')} if isinstance(i, dict) else {'name': default, 'modulcode': default, 'mongoDB-ID': i} for i in modules]
                else:
                    # modules = '\n'.join(['        --- Modul ---\n' + '\n        '.join(Module(i).infocard.split(';\n')) for i in modules]) # FIX: outdated as ; was removed. Marked for removal as well
                    modules_json = [Module(i).infocard for i in modules_json] # type: ignore
            """info = f'''\tName: {module_group.get('name_letter')},
\tZu absolvierende ECTS: {module_group.get('min_ects', default) or default} - {module_group.get('max_ects', default) or default},
\tModule {" (MongoDB-IDs)" if information == 'ids' else "<Name, Modulcode, MongoDB-ID>" if information == 'compressed' else ""}: {modules}'''"""
            info_dict = {
                'name': module_group.get('name_letter'),
                'zu_absolvierende_ects': f"{module_group.get('min_ects', default) or default} - {module_group.get('max_ects', default) or default}",
                'module': modules_json
            }
            return info_dict #  if output_format == 'dict' else info

        if not isinstance(module_groups, str):
            if 'compressed' in self.granularities:
                # module_groups_compressed = '\n' + '\n'.join(['    --- Modulgruppe ---\n' + _create_module_group(i, information='compressed') for i in module_groups])
                module_groups_compressed_json = tuple(_create_module_group(i, information='compressed') for i in module_groups) # tuple
                object.__setattr__(self, 'infocard_compressed_modules_text', _create_infocard(mdl_grp=module_groups_compressed))
                object.__setattr__(self, 'infocard_compressed_modules', _create_infocard(mdl_grp=module_groups_compressed_json))
            if 'ids' in self.granularities:
                # module_groups_ids = '\n' + '\n'.join(['    --- Modulgruppe ---\n' + _create_module_group(i, information='ids') for i in module_groups])
                object.__setattr__(self, 'infocard_module_ids_only_text', _create_infocard(mdl_grp=module_groups_ids))
                module_groups_ids_json = tuple(_create_module_group(i, information='ids') for i in module_groups)
                object.__setattr__(self, 'infocard_module_ids_only', _create_infocard(mdl_grp=module_groups_ids_json))
            if 'all' in self.granularities:
                module_groups_json = tuple(_create_module_group(i, information='all') for i in module_groups)
                # module_groups = '\n' + '\n'.join(['    --- Modulgruppe ---\n' + _create_module_group(i, information='all') for i in module_groups])
                object.__setattr__(self, 'infocard_text', _create_infocard(mdl_grp=module_groups))
                object.__setattr__(self, 'infocard', _create_infocard(mdl_grp=module_groups_json))
        if start_semester is not None:
            start_semester = str(start_semester)
            is_winter_start = bool(start_semester[-1])
            year = start_semester[:4]
            start_semester = ('Wintersemester ' if is_winter_start else 'Sommersemester ') + str(year) + (f'/{int(year) + 1}' if is_winter_start else '')


    """def __str__(self) -> str:
        return self.infocard_text"""


# NOTE: search_field Literal options originate from embedding_ fields in mongo_db/create_collection.py
@tool
async def get_studiengang_modulhandbuch(
    # module_handbook: str | None = None,
    name: str | None = None,
    description: str | None = None,
    faculties: str | None = None,
    path: str | None = None,
    start_semester: int | tuple[int | None, int | None] | None = None, # (datetime.now(ZoneInfo('Europe/Berlin')).year - (1 if (curr_time := datetime.now(ZoneInfo('Europe/Berlin')).month) < 3 else 0)) * 10 + (0 if curr_time < 7 else 1),
    k: int = 3) -> str | ValueError:
    '''
    Findet passende Modulhandbücher für einen bestimmten Studiengang - ÜBERSICHTSVERSION.
    Um die Details der gefundenen besten Modulhandbücher einzusehen, verwende anschließend get_modulhandbuch_by_mongodb_id
    Verwende mindestens einen semantischen Parameter (module_handbook, name, description, faculties, path).
    STRATEGIE:
    - Finde die besten Modulhandbücher (MHB) für den Studiengang
    - Kann mit start_semester gefiltert werden für aktuelles Handbuch
    EINSATZGEBIET:
    - Name des Studiengangs
    - Modulhandbuchgruppe
    - Fakultäten des Studiengangs
    - Dateipfad des Modulhandbuchs
    INPUTS (SEMANTISCH ERFORDERLICH):
    Mindestens EINER von:
      - name (str): Name des Modulhandbuchs
      - description (str): Ab wann man den Studiengang studieren kann; description ist NICHT der Inhalt des Studiengangs, sondern wann er gegründet wurde
      - faculties (str): Die Fakultäten des Studiengangs
      - path (str): Der Pfad des Modulhandbuchs
    INPUTS (OPTIONAL ALS FILTER):
    - start_semester (int oder tuple): Startsemester des Modulhandbuchs
      Format: YYYY1 für Wintersemester, YYYY0 für Sommersemester
      Beispiel: 20261 = WS 2026/27, 20260 = SS 2026
      Tuple: (min, max)  für Bereich, oder exakter Wert mit int oder nicht spezifiziert mit None
    - k (int, default=3): Anzahl der Ergebnisse (MAXIMAL 3 empfohlen, da Dokumente sehr lang)
    OUTPUTS:
      Name
      MongoDB-ID
      Beginn
      Fakultäten
      Modulhandbuchgruppe
      Dateipfad
    HINWEISE:
    - start_semester ist SEHR WICHTIG für korrekte Semesterzuordnung
    - NIE mehrmals in einem ähnlichen Thema aufrufen (Ergebnisse sehr ähnlich)
    - MongoDB-IDs NICHT in Antworten an Nutzer geben
    - Um Modulgruppen und Gründung des Studiengangs zu finden, muss get_modulhandbuch_by_mongodb_id aufgerufen werden
    - Alle Felder, die fehlen, haben keine Informationen inne

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
    rename_keys = {key: v for key, v in zip(embedded_keys['mhbs'], embedded_keys_paths['mhbs'])} | {'module_handbook': 'embedding'}
    # bm25 = ['name', 'description', 'faculties', 'path']
    bm25 = bm25_keys['mhbs']
    for i in bm25:
        # if i == 'name': continue # TODO: make nicer, don't manually exclude fields, that need both or only vector search
        rename_keys.pop(i, None)
    if not any(attribs.get(key) is not None for key in (rename_keys.keys() | bm25)):
        raise ValueError('At least one of name, description or faculties must be provided for semantic or lexicographic search.')
    # NOTE: hardcode weights to make it easier for model as this is set manually and shall not be influenced by the model
    # TODO: refine weights
    weights = {'module_handbook': 1.0, 'name': 1.0, 'description': 0.5, 'faculties': 0.6, 'path': 0.8}
    # NOTE: check manual implementation: each embedding field must have a weight
    if set(rename_keys.keys()).union(set(bm25)) != set(weights.keys()): # use sets for avoiding order
        raise ValueError(f'Weights must be specified for all embedding fields. Missing weights for: {set(rename_keys.keys()) - set(weights.keys())}')
    agg_pipeline = _create_vector_search(attribs=attribs, rename_keys=rename_keys, bm25_keys=bm25, weights=weights, k=k)
    agg_pipeline.extend(mhb_lookup_pipeline)
    cursor = mhbs_db.aggregate(agg_pipeline)
    results = cursor.to_list(length=k)
    outputs = [ModuleHandbook(i, granularities=['compressed']).infocard_compressed_modules for i in results]
    return json.dumps(outputs)


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
Gibt Informationen zu passenden Modulen zurück - ÜBERSICHTSVERSION.
Um zu den besten gefundenen Modulen detaillierte Informationen zu erlangen, verwende das Tool get_modul_by_mongodb_id.
Mittels get_modul_by_mongodb_id erhältst du zusätzliche Informationen zu <Inhalt>, <Ziele>, Workloads, Klausurbeschreibung, Voraussetzungen, Bestehensvoraussetzungen, Dozent, International, Prüfungen.
STRATEGIE:
- Wird aufgerufen, wenn nach Modulen gesucht wird
- Bietet eine Übersicht, die mittels get_modul_by_mongodb_id spezifiziert werden kann
EINSATZGEBIET:
- Modulcode
- Dozenten und Lehrstühle
- Voraussetzungen und Erfolgsvoraussetzungen
- ECTS-Punkte und Semesterverfügbarkeit
- Sprachen und Internationalität
INPUTS (SEMANTISCH ERFORDERLICH):
Mindestens EINER von:
  - name (str): Name des Moduls
  - content (str): Inhalt des Moduls
  - goals (str): Ziele des Moduls
  - lecturer (str): Dozent des Moduls
  - prerequisites (str): Voraussetzungen des Moduls
  - faculty_chair (str): Lehrstuhl des Moduls
  - workloads (str): Arbeitsbelastung des Moduls
  - success_requirements (str): Erfolgsvoraussetzungen
  - exam_outline (str): Prüfungsordnung
INPUTS (OPTIONAL ALS FILTER):
- mandatory (bool): Ob das Modul verpflichtend ist
- module_code (str): Der Modulcode (auch Teil-codes möglich)
- ects (int oder tuple): ECTS-Punkte
- available_semesters (int oder tuple): Verfügbare Semester
- recommended_semester_span (int oder tuple): Empfohlene Semesteranzahl
- languages (list): Sprachen des Moduls
- international (bool): Ob das Modul international ist
- weekly_hours (int oder tuple): Wöchentliche Stunden
- workload_hours (int oder tuple): Arbeitsstunden
- exams (list[int]): Prüfungs-IDs
- k (int, default=5): Anzahl der Ergebnisse
OUTPUTS:
Format Infocard (ÜBERSICHT - excluded Felder):
  Name
  Modulcode
  MongoDB-ID
  ECTS
  Lehrstuhl
  Verpflichtend
  Wochenarbeitsstunden
  Empfohlener Absolvierungszeitraum von bis Semester
  Dauer in Semestern
  Sprachen
  Angeboten in Semestern
  Workload-Stunden
HINWEISE:
- Mindestens einen semantischen Parameter angeben
- MongoDB-IDs NICHT in Antworten an Nutzer geben
- Für Übersicht verwenden
- Für detaillierte Informationen passender hier gefundener Module: get_modul_by_mongodb_id verwenden
- Alle Felder, die fehlen, haben keine Informationen inne

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
       module_lookup
    )
    cursor = modules_db.aggregate(agg_pipeline)
    results = cursor.to_list(length=k)
    outputs = [Module(i).infocard for i in results]
    return json.dumps(outputs)


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
    EINSATZGEBIET:
    - Klausurvorbereitung
    - Prüfungsordnungen
    - Termine und Deadlines
    INPUTS (SEMANTISCH ERFORDERLICH):
    Mindestens EINER von:
      - name (str): Name der Klausur
      - description (str): Beschreibung der Klausur
      - preparation (str): Vorbereitung auf die Klausur
      - type (str): Typ der Klausur (mündlich, schriftlich, Hausarbeit, Seminararbeit, ...)
      - duration (str): Dauer der Klausur
      - frequency (str): Häufigkeit der Klausur
    INPUTS (OPTIONAL ALS FILTER):
    - deadline (int oder tuple): Deadline der Klausur
    - graded (bool): Ob die Klausur benotet ist
    - id (int): ID der Klausur
    - portion_of_grade (int oder tuple): Anteil an der Note der Klausur
    - k (int, default=5): Anzahl der Ergebnisse
    OUTPUTS:
    Format Infocard:
      Name
      Klausur
      MongoDB
      Beschreibung
      Klausurart
      Dauer
      Benotet
      Vorbereitung
      Notenanteil
      Turnus
    HINWEISE:
    - Mindestens einen semantischen Parameter angeben
    - MongoDB-IDs NICHT in Antworten an Nutzer geben
    - Alle Felder, die fehlen, haben keine Informationen inne

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
    return json.dumps(outputs)


@tool
def get_klausur_by_mongodb_id(mongo_id: str) -> str | None:
    '''
    Gibt Informationen zu einer Klausur anhand der MongoDB-ID zurück.
    Gibt Informationen zu einer Klausur anhand der MongoDB-ID zurück.
    Die MongoDB-ID sollte von dem Tool get_modul_by_mongodb_id stammen.
    STRATEGIE:
    - Wird für einzelne Klausuren aufgerufen, die im Modul gefunden wurden
    EINSATZGEBIET:
    - Wenn ID bekannt ist (von anderen Tools erhalten)
    - Detaillierte Abfrage einer spezifischen Klausur
    - Nach `get_modul_by_mongodb_id`
    INPUTS:
    - mongo_id (str): Die MongoDB-ID der Klausur
    OUTPUTS:
        Name
        Klausur
        MongoDB
        Beschreibung
        Klausurart
        Dauer
        Benotet
        Vorbereitung
        Notenanteil
        Turnus

    HINWEISE:
    - MongoDB-IDs nur intern verwenden
    - Alle Felder, die fehlen, haben keine Informationen inne

    Args:
        mongo_id (str): Die MongoDB-ID der Klausur, nach der gesucht werden soll.
    Returns:
        str | None: Informationen zu der Klausur. None, wenn keine Klausur mit der angegebenen MongoDB-ID gefunden wurde.
    '''
    result = exams_db.find_one({'_id': ObjectId(mongo_id)})
    if result:
        return json.dumps(Exam(result).infocard)
    return 'Keine Informationen zu der Klausur gefunden.'

@tool
def get_modul_by_mongodb_id(mongo_id: str) -> str | None:
    '''
    Gibt Informationen zu einem Modul anhand der MongoDB-ID zurück.
    Gibt Informationen zu einem Modul anhand der MongoDB-ID zurück - DETAILVERSION.
    Die MongoDB-ID sollte aus dem Tool get_modulhandbuch_by_mongodb_id stammen.
    STRATEGIE:
    - Wird für einzelne Module aufgerufen, die im Modulhandbuch gefunden wurden
    EINSATZGEBIET:
    - Wenn ID bekannt ist (von anderen Tools erhalten)
    - Detaillierte Abfrage eines spezifischen Moduls
    - Nach `get_studiengang_modulhandbuch` und ggf. `get_modulhandbuch_by_mongodb_id`
    - Untersucht die besten gefundenen Ergebnisse aus get_modul
    INPUTS:
    - mongo_id (str): Die MongoDB-ID des Moduls
    OUTPUTS:
        Name
        Modulcode
        MongoDB-ID
        ECTS
        Lehrstuhl
        Verpflichtend
        Wochenarbeitsstunden
        Voraussetzungen
        Bestehensvoraussetzungen
        Empfohlener
        Dauer
        Inhalt
        Ziele
        Dozent
        Sprachen
        International
        Angeboten
        Wochenstunden
        Workload
        Workloads
        Klausurbeschreibung
        Prüfungen: Liste aller Klausuren in diesem Modul mit Klausur-ID, MongoDB-ID, Beschreibung, Klausurart, Dauer, Benotet, Vorbereitung, Notenanteil an Modul und Turnus (wie häufig die Klausur gehalten wird)
    WICHTIG:
    - Für detaillierte Untersuchung verwenden
    - Workloads werden vollständig ausgeschrieben (nicht zusammengefasst)
    HINWEISE:
    - IDs nur intern verwenden
    - NICHT in Antworten an Nutzer geben
    - None zurückgegeben, wenn nicht gefunden
    - Für detaillierte Informationen verwenden
    - Um mehr Informationen zu den Klausuren zu erhalten, rufe get_klausur_by_mongodb_id auf
    - Alle Felder, die fehlen, haben keine Informationen inne

    Args:
        mongo_id (str): Die MongoDB-ID des Moduls, nach der gesucht werden soll.
    Returns:
        str | None: Informationen zu dem Modul. None, wenn kein Modul mit der angegebenen MongoDB-ID gefunden wurde.
    '''
    aggregation_pipeline = [
        {'$match': {'_id': ObjectId(mongo_id)}},
        module_lookup
    ]
    result = modules_db.aggregate(aggregation_pipeline).to_list(length=1)[0]
    if result:
        return json.dumps(Module(result, compact=False).infocard)
    return 'Keine Informationen zu dem Modul gefunden.'

@tool
def get_modulhandbuch_by_mongodb_id(mongo_id: str) -> str | None:
    '''
    Gibt Informationen zu einem Modulhandbuch anhand der MongoDB-ID zurück.
    Gibt ausführliche Informationen zu einem Modulhandbuch anhand der MongoDB-ID zurück - DETAILVERSION.
    Die ModulDB-ID für den Aufruf sollte von dem Tool get_studiengang_modulhandbuch stammen
    STRATEGIE:
    - VIERTE STUFE nach get_studiengang_modulhandbuch
    - Wird mit dem besten gefundenen MHB aufgerufen
    - Gibt vollständige Details ohne Kompaktierung (compact=False)
    EINSATZGEBIET:
    - Wenn ID bekannt ist (von anderen Tools erhalten)
    - Detaillierte Abfrage eines spezifischen Modulhandbuchs
    - Nach `get_studiengang_modulhandbuch` mit dem besten Ergebnis
    INPUTS:
    - mongo_id (str): Die MongoDB-ID des Modulhandbuchs
    OUTPUTS:
    Format Infocard (vollständig, compact=False):
      Name
      MongoDB
      Beginn
      Fakultäten
      Modulhandbuchgruppe
      Dateipfad
      Gründung
      Modulgruppen: beinhaltet Liste aller Modulgruppen mit Name (Buchstabe), Bereich der zu absolvierenden ECTS, alle enthaltenen Module mit <Name, Modulcode, MongoDB-ID>
    HINWEISE:
    - IDs nur intern verwenden
    - None zurückgegeben, wenn nicht gefunden
    - Nach `get_studiengang_modulhandbuch` mit dem besten Ergebnis aufrufen
    - Alle Felder, die fehlen, haben keine Informationen inne

    Args:
        mongo_id (str): Die MongoDB-ID des Modulhandbuchs, nach der gesucht werden soll.
    Returns:
        str | None: Ausführliche Informationen zu dem Modulhandbuch. None, wenn kein Modulhandbuch mit der angegebenen MongoDB-ID gefunden wurde.
    '''
    aggregation_pipeline = [
        {'$match': {'_id': ObjectId(mongo_id)}},
        *mhb_lookup_pipeline
    ]
    result = mhbs_db.aggregate(aggregation_pipeline).to_list(length=1)[0]
    if result:
        return json.dumps(ModuleHandbook(result, compact=False).infocard) # _compressed_modules
    return 'Keine Informationen zu dem Modulhandbuch gefunden.'


def replacer(match):
    label, url = match.group(1), match.group(2)
    absolute = urljoin('https://www.uni-augsburg.de', url)
    return f'URL to {label}: {absolute}'


# TODO: use search engine to search for query then only allow uni augsburg links in the found urls or specify site: but that changes results to the worse
r"""@DeprecationWarning
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
    return json.dumps(results)


@tool
def get_datum() -> str:
    '''
    Gibt das aktuelle Datum zurück.

    Returns:
        str: Das aktuelle Datum im Format "DD-MM-YYYY".
    '''
    return datetime.now(ZoneInfo("Europe/Berlin")).strftime("%d-%m-%Y")
