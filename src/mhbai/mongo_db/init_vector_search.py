import os

from dotenv import load_dotenv
from pymongo import MongoClient

env_path = os.path.join('./', '.env')
load_dotenv(dotenv_path=env_path)

password = os.getenv('MONGO_DB_ADMIN_PASSWORD')

client = MongoClient(
    'mongodb://localhost:27017/?replicaSet=rs0',
    username='admin',
    password=password,
    authSource='admin'
)

collections = ['mhbs', 'modules', 'exams']
# TODO: maybe only show partial path for security reasons
embedded_keys = {'mhbs': ['description', 'faculties', 'name', 'path'],
                 'modules': ['content', 'goals', 'exam_outline', 'faculty_chair', 'lecturer', 'name', 'prerequisites', 'success_requirements', 'workloads'],
                 'exams': ['description', 'duration', 'frequency', 'name', 'preparation', 'type']}

embedded_keys_paths = {key: ['embedding_' + e for e in value] + ['embedding'] for key, value in embedded_keys.items()}

bm25_keys = {'mhbs': ['name', 'description', 'faculties', 'path'],
              'modules': ['name', 'lecturer', 'prerequisites', 'faculty_chair', 'success_requirements'],
              'exams': ['name', 'type', 'duration', 'frequency']}

filter_keys = {'mhbs': ['start_semester'],
              'modules': ['available_semesters', 'ects', 'exams', 'international', 'languages', 'mandatory', 'module_code', 'recommended_semester_span', 'weekly_hours', 'workload_hours'],
              'exams': ['deadline', 'graded', 'id', 'portion_of_grade']}

if __name__ == '__main__':
    for collection in collections:
        coll = client['unia'][collection]
        res = coll.create_search_index({
            'name': 'vector_index',
            'type': 'vectorSearch',
            'definition': {
                'fields': [
                    *[{
                        'type': 'vector',
                        'path': key,
                        # NOTE: match this to the model using: bash: ollama show qwen3-embedding | grep 'embedding length' (for qwen3 embeddings)
                        'numDimensions': 4096,
                        'similarity': 'cosine',
                    } for key in embedded_keys_paths[collection]],
                    *[{
                        'type': 'filter',
                        'path': key
                    } for key in filter_keys[collection] + ['_hash']]
                ]
            }
        })
        bm25_res = coll.create_search_index({
            'name': 'bm25_index',
            'type': 'search',
            'definition': {
                'mappings': {
                    'dynamic': True,
                    'fields': {
                        **{key: {'type': 'string'} for key in bm25_keys[collection]}
                    }
                }
            }
        })
        print(f"Created search index for collection '{collection}': {res} & {bm25_res}")
