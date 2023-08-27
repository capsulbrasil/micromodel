import typing
import types
from abc import ABCMeta
from pymongo import ReturnDocument
from pymongo.collection import Collection
from pymongo.results import UpdateResult

T = typing.TypeVar('T')

ValidationOptions = typing.TypedDict('ValidationOptions', {
    'allow_missing': typing.NotRequired[bool],
    'allow_extraneous': typing.NotRequired[bool]
})

class Model(typing.Generic[T]):
    coll: Collection

    def __init__(self, model_type: typing.Callable[[typing.Any], T], ct: dict[str, typing.Any] = {}, coll: Collection | None = None):
        self.model_type = model_type
        self.ct = ct
        if coll:
            self.coll = coll

    def cast(self, target: T | typing.Any): return typing.cast(T, target)
    def strict_cast(self, target: T): return target
    def validate(self, target: T, options: ValidationOptions = {}): return validate(self.model_type, typing.cast(typing.Any, target), options, self.ct)

    def find(self, *args: typing.Any, **kwargs: typing.Any):
        result = self.coll.find(*args, **kwargs)
        return typing.cast(typing.Generator[T, None, None], result)

    def find_one(self, *args: typing.Any, **kwargs: typing.Any):
        result = self.coll.find_one(*args, **kwargs)
        if not result:
            return None
        return self.cast(result)

    def insert_one(self, what: T, *args: typing.Any, **kwargs: typing.Any):
        what = self.validate(what)
        result = self.coll.insert_one(typing.cast(typing.Any, what), *args, **kwargs)
        return result

    def _update(self, value: typing.Any, query_fields: list[str], ret: bool = True):
        new = {
            k: v
            for k, v in value.items()
            if k not in [
                '_id',
                *query_fields
            ]
        }

        search = {
            '$and': [
                { f: value[f] }
                for f in query_fields
                if f in value
            ]
        }

        if ret:
            return self.coll.find_one_and_update(
                search,
                { '$set': new },
                return_document=ReturnDocument.AFTER,
                upsert=True
            )
        else:
            return self.coll.update_one(
                search,
                { '$set': new },
                upsert=True
            )

    def update(self, value: typing.Any, query_fields: list[str]):
        result = self._update(value, query_fields, ret=True)
        return typing.cast(UpdateResult, result)

    def upsert(self, value: typing.Any, query_fields: list[str]):
        result = self._update(value, query_fields, ret=True)
        return typing.cast(T, result)


def raise_missing_key(k: int | str):
    raise TypeError('missing key: %s' % k)

def raise_extraneous_key(k: int | str):
    raise TypeError('extraneous key: %s' % k)

def raise_type_error(k: int | str, args: str, v: typing.Any):
    raise TypeError('incorrect type for %s: expected %s, got %s' % (k, args, v))

def unwrap_type(obj: dict[int | str, typing.Any] | list[typing.Any], k: int | str, v: typing.Any, options: ValidationOptions = {}, ct: dict[str, typing.Any] = {}):
    origin = typing.get_origin(v)
    args = typing.get_args(v)

    if (isinstance(obj, dict) and not k in obj) or (isinstance(obj, list) and int(k) > len(obj)):
        if types.NoneType not in args and not options.get('allow_missing'):
            raise_missing_key(k)
        return

    value = obj[int(k)] \
        if isinstance(obj, list) \
        else obj[k]

    match origin:
        case _ if origin == list:
            for i in range(len(value)):
                unwrap_type(value, i, args[0], options, ct)

        case _ if origin == tuple:
            for i in range(len(value)):
                unwrap_type(value, i, args[i], options, ct)

        case typing.Literal:
            if value not in args:
                raise_type_error(k, str(v), value)

        case types.UnionType:
            for candidate in args:
                if isinstance(candidate(), type(value)):
                    unwrap_type(obj, k, candidate, options, ct)
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
         obj[k] = unwrap_type(obj, k, v, options, ct)

    return typing.cast(T, obj)

def get_hints(model_type: ABCMeta):
    hints = typing.get_type_hints(model_type)
    return hints

def model(model_type: typing.Callable[[typing.Any], T], ct: dict[str, typing.Any] = {}, coll: Collection | None = None) -> Model[T]:
    return Model(model_type, ct, coll)

