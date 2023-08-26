import os
import typing
from unittest import TestCase
from src.micromodel import model
from pymongo import MongoClient

client = MongoClient('mongodb://%s:%s/test' % (
    os.getenv('MONGODB_HOST'),
    int(os.getenv('MONGODB_PORT', '0'))
))

db = client.get_default_database()

Animal = typing.TypedDict('Animal', {
    'name': str,
    'specie': typing.Literal[
        'dog',
        'bird'
    ]
})

db.drop_collection('animals')
m = model(Animal, coll=db['animals'])

class TestMongodb(TestCase):
    def test_object_equality(self):
        m.insert_one({
            'name': 'thor',
            'specie': 'dog'
        })

        result = m.find_one({
            'name': 'thor'
        })

        if not result:
            raise ValueError()

        self.assertEqual(result['name'], 'thor')
        self.assertEqual(result['specie'], 'dog')


    def test_upsert(self):
        m.upsert({
            'name': 'thor',
            'specie': 'bird'
        }, ['name'])

        result = m.find_one({
            'name': 'thor'
        })

        if not result:
            raise ValueError()

        self.assertEqual(result['name'], 'thor')
        self.assertEqual(result['specie'], 'bird')
