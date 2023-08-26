import typing
import types
from abc import ABCMeta

T = typing.TypeVar('T')

ValidationOptions = typing.TypedDict('ValidationOptions', {
    'allow_extraneous': typing.NotRequired[bool]
})

class Model(typing.Generic[T]):
    def __init__(self, model_type: typing.Callable[[typing.Any], T], ct: dict[str, typing.Any] = {}):
        self.model_type = model_type
        self.ct = ct

    def cast(self, target: T | dict[typing.Never, typing.Never]): return typing.cast(T, target)
    def validate(self, target: T, options: ValidationOptions = {}): return validate(self.model_type, typing.cast(typing.Any, target), options, self.ct)

def raise_missing_key(k: int | str):
    raise TypeError('missing key: %s' % k)

def raise_extraneous_key(k: int | str):
    raise TypeError('extraneous key: %s' % k)

def raise_type_error(k: int | str, args: str, v: typing.Any):
    raise TypeError('incorrect type for %s: expected %s, got %s' % (k, args, v))

def unwrap_type(obj: dict[int | str, typing.Any] | list[typing.Any], k: int | str, v: typing.Any, ct: dict[str, typing.Any] = {}):
    origin = typing.get_origin(v)
    args = typing.get_args(v)

    if (isinstance(obj, dict) and not k in obj) or (isinstance(obj, list) and int(k) > len(obj)):
        if types.NoneType not in args:
            raise_missing_key(k)
        return

    value = obj[int(k)] \
        if isinstance(obj, list) \
        else obj[k]

    match origin:
        case _ if origin == list:
            for i in range(len(value)):
                unwrap_type(value, i, args[0], ct)

        case _ if origin == tuple:
            for i in range(len(value)):
                unwrap_type(value, i, args[i], ct)

        case typing.Literal:
            if value not in args:
                raise_type_error(k, str(v), value)

        case types.UnionType:
            for candidate in args:
                if isinstance(candidate(), type(value)):
                    unwrap_type(obj, k, candidate, ct)
                    break
            else:
                raise_type_error(k, str(args), type(value))

        case None:
            if complex_type := ct.get(v.__name__):
                value = validate(complex_type, value)
                return value

            if not isinstance(value, v):
                raise_type_error(k, str(v), type(value))
        case _:
            if not isinstance(value, origin):
                raise_type_error(k, str(args), type(value))

    return value

def validate(model_type: typing.Callable[[typing.Any], T], target: dict[str, typing.Any], options: ValidationOptions = {}, ct: dict[str, typing.Any] = {}) -> T:
    obj: dict[int | str, typing.Any] = {}
    hints = get_hints(typing.cast(ABCMeta, model_type))

    for k, v in target.items():
        if k not in hints:
            if options.get('allow_extraneous'):
                continue
            raise_extraneous_key(k)
        obj[k] = v

    for k, v in hints.items():
         obj[k] = unwrap_type(obj, k, v, ct)

    return typing.cast(T, obj)

def get_hints(model_type: ABCMeta):
    hints = typing.get_type_hints(model_type)
    return hints

def model(model_type: typing.Callable[[typing.Any], T], ct: dict[str, typing.Any] = {}) -> Model[T]:
    return Model(model_type, ct)

