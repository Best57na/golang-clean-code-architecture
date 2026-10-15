import re

_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


def camel_to_snake(name: str) -> str:
    return _CAMEL_BOUNDARY.sub("_", name).lower()


def convert_name_to_crud_slug(name: str) -> str:
    """UserTokens / user_tokens -> user-tokens"""
    return camel_to_snake(name).replace("_", "-")
