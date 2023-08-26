# Micromodel

Static and runtime dictionary validation (with MongoDB support).

## Install

```sh
$ pip install micromodel
```

## Why

We had a HUGE Python code base which was using `pydantic` to provide a validation layer for MongoDB operations. The code was all messy but it worked fine, until we decided to switch the type checker config from "basic" to "strict", then over a thousand of dictionary-related errors popped up, not to mention the annoying conversions from `dict` to classes that were going on on every validation and that should be checked everytime.

We then decided to make this validation in-loco using a more vanilla approach with only `TypedDict`s. Now our dictionaries containing MongoDB documents are consistently dicts that match with the static typing.

## Usage (validation only)

```python
import typing
from micromodel import model, ValidationOptions

Animal = typing.TypedDict('Animal', {
    'name': str,
    'specie': list[typing.Literal[
        'dog',
        'cat',
        'bird'
    ]]
})

# even another TypedDicts can be used!
Person = typing.TypedDict('Person', {
    'name': typing.NotRequired[str | None],
    'age': int,
    'animal': Animal
})

m = model(Person, {
    'Animal': Animal
})

# hooks can be implemented using monkeypatching
# setting default values also can be achieved this way
old_validate = m.validate
def new_validate(target: Person, options: ValidationOptions = {}):
    new = target.copy()
    new['name'] = new.get('name', 'unknown')
    return old_validate(new, options)

m.validate = new_validate

result = m.validate({
    'name': 'joao',
    'animal': {
        'name': 'thor',
        'specie': [
            'dog',
            # 'turtle' (this would produce both static and runtime errors)
        ]
    }
})

"""
{
  "name": "Joao",
  "animal": {
    "name": "thor",
    "specie": [
      "dog"
    ]
  }
}
"""
print(result)

"""
{}
"""
print(m.cast({}))
```

## Usage (with MongoDB)

```python
import os
import typing
from micromodel import model
from pymongo import MongoClient

db = MongoClient(os.getenv('MONGODB_URI')).get_default_database()

Animal = typing.TypedDict('Animal', {
    'name': str,
    'specie': list[typing.Literal[
        'dog',
        'cat',
        'bird'
    ]]
})

m = model(Animal, coll=db['animals'])
m.insert_one({
    'name': 'thor',
    'specie': 'dog'
})
```

## License

This library is [MIT licensed](https://github.com/capsulbrasil/normalize-json/tree/master/LICENSE).
