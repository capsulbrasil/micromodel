# Micromodel

Static and runtime dictionary validation.

## Install

```sh
$ pip install micromodel
```

## Why

We had a HUGE Python code base which was using `pydantic` to provide a validation layer for MongoDB operations. The code was all messy but it worked fine, until we decided to switch the type checker config from "basic" to "strict", then over a thousand of dictionary-related errors popped up, not to mention the annoying conversions from `dict` to classes that were going on on every validation and that should be checked everytime.

We then decided to make this validation in-loco using a more vanilla approach with only `TypedDict`s. Now our dictionaries containing MongoDB documents are consistently dicts that match with the static typing.

## Usage

```python
import typing
from micromodel import model

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
    'name': str,
    'age': int,
    'animal': Animal
})

m = model(Person, {
    'Animal': Animal
})

old_validate = m.validate
def new_validate(target: Person):
    new = target.copy()
    new['name'] = new['name'].capitalize()
    return validate(Person, typing.cast(typing.Any, new))

# hooks can be implemented using monkeypatching
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
```

## License

This library is [MIT licensed](https://github.com/capsulbrasil/normalize-json/tree/master/LICENSE).
