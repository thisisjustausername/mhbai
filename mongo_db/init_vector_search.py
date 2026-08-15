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

for collection in collections:
    coll = client['unia'][collection]
    coll.create_search_index({
        'name': 'vector_index',
        'type': 'vectorSearch',
        'definition': {
            'fields': [
                {
                    'type': 'vector',
                    'path': 'embedding',
                    # NOTE: match this to the model using: bash: ollama show qwen3-embedding | grep 'embedding length' (for qwen3 embeddings)
                    'numDimensions': 4096,
                    'similarity': 'cosine',
                }
            ]
        }
    })
