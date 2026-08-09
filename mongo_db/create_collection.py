'''
Create mongodb for compressed STUDIS mhb json files and extracted json files.
'''

from pymongo import ASCENDING, IndexModel, MongoClient

client = MongoClient('mongodb://localhost:27017/')

# create / access db
db = client['unia']

# create / access collections

db.create_collection(
    'mhbs',
    validator={
        '$jsonSchema': {
            'bsonType': 'object',
            'required': ['compressed_path', 'path', 'name', 'start_semester', 'faculties', 'mhb_group', 'module_groups'],
            'properties': {
                'compressed_path': {
                    'bsonType': 'string',
                    'description': 'path to the compressed extracted json mhb file'
                },
                'path': {
                    'bsonType': 'string',
                    'description': 'path to the extracted json mhb file'
                },
                'name': {
                    'bsonType': 'string',
                    'description': 'name of the mhb'
                },
                'start_semester': {
                    'bsonType': ['string', 'null'],
                    'description': 'the first semester the mhb starts',
                    'pattern': r'^(Wintersemester \d{4}/\d{2,4}|Sommersemester \d{4})$'
                },
                'faculties': {
                    'bsonType': 'array',
                    'description': 'the faculties the mhb belongs to',
                    'minItems': 1,
                    'items': {
                        'bsonType': 'string'
                    }
                },
                'mhb_group': {
                    'bsonType': ['string', 'null'],
                    'description': 'the mhb group the mhb belongs to'
                },
                'description': {
                    'bsonType': ['string', 'null'],
                    'description': 'the description of the mhb'
                },
                'module_groups': {
                    'bsonType': ['array', 'null'],
                    'description': 'the module groups the mhb contains',
                    'minItems': 1,
                    'items': {
                        'bsonType': 'object',
                        'required': ['name_letter', 'modules'],
                        'properties': {
                            'name_letter': {
                                'bsonType': 'string',
                                'description': 'letter for the module group'
                            },
                            'min_ects': {
                                'bsonType': ['int', 'null'],
                                'description': 'minimum ects for the module group'
                            },
                            'max_ects': {
                                'bsonType': ['int', 'null'],
                                'description': 'maximum ects for the module group'
                            },
                            'modules': {
                                'bsonType': ['array', 'null'],
                                'description': 'the modules the module group contains',
                                'minItems': 1,
                                'items': {
                                    'bsonType': 'objectId',
                                    'description': 'the module id linking to the modules collection for the module contained in module_group'
                                }
                            }
                        }
                    }
                }
            }
        }
    })
mhbs = db['mhbs']
mhbs.create_indexes([
    IndexModel([('compressed_path', ASCENDING)], unique=True),
    IndexModel([('path', ASCENDING)], unique=True)
])


# NOTE: ignore parts, description, module_part_combinations, keywords, usability as they are always either None or []
# NOTE: ignore prerequisite_language as it mostly contains the same information as prerequisites
# NOTE: simply pick first item from faculty_chair as it is always only one item
db.create_collection(
    'modules',
    validator={
        '$jsonSchema': {
            'bsonType': 'object',
            'required': ['name', 'module_code', 'ects', 'exams', '_hash'],
            'properties': {
                'name': {
                    'bsonType': 'string',
                    'description': 'name of the module'
                },
                'module_code': {
                    'bsonType': 'string',
                    'description': 'module code of the module',
                    'pattern': r'^[A-ZÄÖÜ]{3}-\d{4}([a-zöäüA-ZÖÄÜ]|_\d{2})?|^[A-ZÄÖÜ]{5}-\d{4}$'
                },
                'ects': {
                    'bsonType': 'int',
                    'description': 'ects of the module',
                    'minimum': 0
                },
                'mandatory': {
                    'bsonType': ['bool', 'null'],
                    'description': 'whether the module is mandatory or not'
                },
                'weekly_hours': {
                    'bsonType': ['int', 'null'],
                    'description': 'weekly hours for the module',
                    'minimum': 0
                },
                'workload_hours': {
                    'bsonType': ['int', 'null'],
                    'description': 'workload hours for the module',
                    'minimum': 0
                },
                'prerequisites': {
                    'bsonType': ['string', 'null'],
                    'description': 'prerequisites for the module'
                },
                'success_requirements': {
                    'bsonType': ['string', 'null'],
                    'description': 'requirements for successfully completing the module'
                },
                'recommended_semester_span': {
                    'bsonType': ['object', 'null'],
                    'description': 'in which semester span the module is recommended to be taken with start semester and end semester',
                    'required': ['start_semester', 'end_semester'],
                    'properties': {
                        'start_semester': {
                            'bsonType': ['int', 'null'],
                            'description': 'the first semester the module is recommended to be taken',
                            'minimum': 1
                        },
                        'end_semester': {
                            'bsonType': ['int', 'null'],
                            'description': 'the last semester the module is recommended to be taken; 99 means no upper bound',
                            'minimum': 1
                        }
                    }
                },
                'duration_in_semesters': {
                    'bsonType': ['int', 'string', 'null'], # TODO: create better fix for duration of e.g. 1-2
                    'description': 'how many semesters this module takes'
                },
                'content': {
                    'bsonType': ['string', 'null'],
                    'description': 'content of the module'
                },
                'lecturer': {
                    'bsonType': ['string', 'null'],
                    'description': 'lecturer of the module'
                },
                'exam_outline': {
                    'bsonType': ['string', 'null'],
                    'description': 'what the exam will look like (e.g. Klausur, mündlich, Hausarbeit, etc.)'
                },
                'goals': {
                    'bsonType': ['string', 'null'],
                    'description': 'goals the module aims to teach'
                },
                'international': {
                    'bsonType': 'bool',
                    'description': 'whether international students should take this module or not'
                },
                'languages': {
                    'bsonType': ['array', 'null'],
                    'description': 'The languages needed for this module',
                    'items': {
                        'bsonType': 'string',
                        'description': 'language needed for this module'
                    }
                },
                'available_semesters': {
                    'bsonType': 'object',
                    'description': 'in which semesters the module is offered, with a start and an end semester, combined with frequency, construction of all available semesters possible',
                    'required': ['start_semester', 'end_semester', 'frequency'],
                    'properties': {
                        'start_semester': {
                            'bsonType': ['string', 'null'],
                            'description': 'the first semester the module is offered',
                            'pattern': r'^(Wintersemester \d{4}/\d{2,4}|Sommersemester \d{4})$'
                        },
                        'end_semester': {
                            'bsonType': ['string', 'null'],
                            'description': 'the last semester the module is offered; if None, the module is offered indefinitely',
                            'pattern': r'^(Wintersemester \d{4}/\d{2,4}|Sommersemester \d{4})$'
                        },
                        'frequency': {
                            'bsonType': ['string', 'null'],
                            'description': 'how often the module is offered (e.g. every semester, every year, etc.)'
                        }
                    }
                },
                'faculty_chair': {
                    'bsonType': 'string',
                    'description': 'the faculty chair responsible for the module'
                },
                'workloads': {
                    'bsonType': ['array', 'null'],
                    'description': 'the workloads the module contains',
                    'minItems': 1,
                    'items': {
                        'bsonType': 'object',
                        'required': ['name', 'in_presence', 'time_expenditure'],
                        'properties': {
                            'name': {
                                'bsonType': 'string',
                                'description': 'name of the workload'
                            },
                            'in_presence': {
                                'bsonType': 'bool',
                                'description': 'whether the workload is in presence or not'
                            },
                            'time_expenditure': {
                                'bsonType': 'int',
                                'description': 'time expenditure for the workload in hours',
                                'minimum': 0
                            }
                        }
                    }
                },
                'exams': {
                    'bsonType': ['array', 'null'],
                    'description': 'the exams the module contains',
                    'minItems': 1,
                    'items': {
                        'bsonType': 'objectId',
                        'description': 'the exam id linking to the exams collection for the exam contained in module'
                    }
                },
                '_hash': {
                    'bsonType': 'string',
                    'description': 'hash of the module, used for uniqueness checks'
                }
            }
        }
    }
)

modules = db['modules']
modules.create_index('_hash', unique=True)


# NOTE: ignore languages as it is always None
db.create_collection(
    'exams',
    validator={
        '$jsonSchema': {
            'bsonType': 'object',
            'required': ['name', 'id', 'graded', 'type', '_hash'],
            'properties': {
                'name': {
                    'bsonType': 'string',
                    'description': 'name of the exam'
                },
                'id': {
                    'bsonType': 'int',
                    'description': 'exam id from STUDIS',
                    'minimum': 10,
                    'maximum': 99999
                },
                'graded': {
                    'bsonType': 'bool',
                    'description': 'whether the exam is graded',
                },
                'type': {
                    'bsonType': 'string',
                    'description': 'type of the exam (e.g. Klausur, mündlich, Hausarbeit, etc.)'
                },
                'duration': {
                    'bsonType': ['string', 'null'],
                    'description': 'duration of the exam, time unit is being specified in the string (e.g. 90 Minuten, 2 Stunden, etc.)',
                },
                'portion_of_grade': {
                    'bsonType': ['int', 'null'],
                    'description': 'portion of the grade the exam contributes to the module grade, in percent',
                    'minimum': 0,
                    'maximum': 100
                },
                'preparation': {
                    'bsonType': ['string', 'null'],
                    'description': 'preparation for the exam'
                },
                'deadline': {
                    'bsonType': ['int', 'null'],
                    'description': 'deadline for the exam',
                    'minimum': 0
                },
                'description': {
                    'bsonType': ['string', 'null'],
                    'description': 'description of the exam'
                },
                'frequency': {
                    'bsonType': ['string', 'null'],
                    'description': 'how often the exam is offered (e.g. every semester, every year, etc.); LV: Lehrveranstaltung, SoSe: Sommersemester, WiSe: Wintersemester'
                },
                '_hash': {
                    'bsonType': 'string',
                    'description': 'hash of the exam, used for uniqueness checks'
                }
            }
        }
    }
)

exams = db['exams']
exams.create_index('_hash', unique=True)
