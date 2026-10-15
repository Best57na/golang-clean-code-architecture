import types
from datetime import date, datetime
from typing import Any, Union, get_args, get_origin

_AVRO_TYPES: list[tuple[type, str]] = [
    # bool before int: bool is a subclass of int
    (bool, "boolean"),
    (int, "int"),
    (float, "double"),
    (str, "string"),
    (datetime, "datetime"),
    (date, "date"),
    (dict, "map"),
    (list, "array"),
]


def unwrap_type(python_type: Any) -> Any:
    """Optional[X] / X | None -> X, list[X] -> list."""
    if get_origin(python_type) in (Union, types.UnionType):
        non_null = [arg for arg in get_args(python_type) if arg is not type(None)]
        python_type = non_null[0] if len(non_null) == 1 else object
    return get_origin(python_type) or python_type


def avro_type(python_type: Any) -> str:
    python_type = unwrap_type(python_type)
    for candidate, name in _AVRO_TYPES:
        if isinstance(python_type, type) and issubclass(python_type, candidate):
            return name
    return "unknown"


def generate_avro_schema(name: str, fields: list[tuple[str, Any]]) -> dict[str, Any]:
    return {
        "type": "record",
        "name": name,
        "fields": [
            {"name": field_name, "type": avro_type(field_type)} for field_name, field_type in fields
        ],
    }
