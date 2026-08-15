from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['unia']

db.drop_collection('exams')
db.drop_collection('modules')
db.drop_collection('mhbs')
