import typing
from unittest import TestCase
from src.micromodel import model

Animal = typing.TypedDict('Animal', {
    'name': str,
    'specie': typing.Literal[
        'dog',
        'bird'
    ]
})

Person = typing.TypedDict('Person', {
    'name': str,
    'age': int,
    'hobbies': typing.NotRequired[None | list[typing.Literal[
        'programming',
        'reading',
        'swimming'
    ]]],
    'hour': tuple[int, int]
})

PetOwner = typing.TypedDict('PetOwner', {
    'name': str,
    'pet': list[Animal]
})

class TestValidation(TestCase):
    def test_object_equality(self):
        m = model(Person)
        target = Person({
            'name': 'hello',
            'age': 5,
            'hobbies': [
                'reading',
            ],
            'hour': (12, 30)
        })

        result = m.validate(target)
        self.assertEqual(target, result)

    def test_reports_missing(self):
        m = model(Person)
        target = Person({ # type: ignore
            'name': 'hello',
            'age': 5,
            'hobbies': [
                'reading',
            ]
        })

        with self.assertRaisesRegex(TypeError, 'missing key: hour'):
            m.validate(target)

    def test_reports_extraneous(self):
        m = model(Person)
        target = Person({
            'name': 'hello',
            'age': 5,
            'hobbies': [
                'reading',
            ],
            'hour': (12, 30),
            'hey': 'heyy' # type: ignore
        })

        with self.assertRaisesRegex(TypeError, 'extraneous key: hey'):
            m.validate(target)

    def test_generics_validation(self):
        m = model(Person)
        target = Person({
            'name': 'hello',
            'age': 5,
            'hobbies': [
                'reading',
            ],
            'hour': (12, 'thirty') # type: ignore
        })

        with self.assertRaisesRegex(TypeError, 'incorrect type for 1'):
            m.validate(target)

    def test_indepth_validation(self):
        m = model(PetOwner, ct={
            'Animal': Animal
        })

        target = PetOwner({
            'name': 'joao',
            'pet': [
                {
                    'name': 'thor',
                    'specie': 'dog'
                },
                {
                    'name': 'spike',
                    'specie': 'dogx' # type: ignore
                }
            ]
        })

        with self.assertRaisesRegex(TypeError, 'got dogx'):
            m.validate(target)
