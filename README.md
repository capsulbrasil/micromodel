# Micromodel

Static and runtime dictionary validation (yet another).

## Install

```sh
$ pip install micromodel
```

## Usage

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

# another TypedDicts can be nested
Person = typing.TypedDict('Person', {
    'name': typing.NotRequired[str | None],
    'age': int,
    'animal': Animal
})

m = model(Person, {
    'Animal': Animal
})

# the validate method will return the input as it is narrowed as the model type
# or raise if it is invalid
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

# the is_valid method will return the input object narrowed as the model type or
# False otherwise
if valid := m.is_valid(result):
    print('dictionary is valid')

# same as typing.cast(Model[T], {})
print(m.cast({}))
```

## License

This library is [MIT licensed](https://github.com/capsulbrasil/normalize-json/tree/master/LICENSE).
