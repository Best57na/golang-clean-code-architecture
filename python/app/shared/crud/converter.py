import re
from datetime import date, datetime
from typing import Any

from app.shared.crud.avro_schema import unwrap_type

_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")
_TRUE_VALUES = {"true", "1"}
_FALSE_VALUES = {"false", "0"}


def camel_to_snake(name: str) -> str:
    return _CAMEL_BOUNDARY.sub("_", name).lower()


def convert_name_to_crud_slug(name: str) -> str:
    """UserTokens / user_tokens -> user-tokens"""
    return camel_to_snake(name).replace("_", "-")


def convert_query_value(python_type: Any, value: str) -> Any:
    """Convert a query-string value to a field's type. Raises ValueError if it does not fit."""
    python_type = unwrap_type(python_type)
    if python_type is bool:
        if value.lower() in _TRUE_VALUES:
            return True
        if value.lower() in _FALSE_VALUES:
            return False
        raise ValueError(f"invalid boolean: {value}")
    if python_type in (datetime, date):
        return python_type.fromisoformat(value)
    if python_type in (int, float, str):
        return python_type(value)
    return value
