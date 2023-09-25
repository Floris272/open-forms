from typing import TypeVar

from django.utils.html import escape

from openforms.typing import JSONValue

T = TypeVar("T", bound=JSONValue)


def html_escape_json(value: T) -> T:
    """
    Recursively apply HTML escaping to string value nodes.
    """
    match value:
        case list():
            return [html_escape_json(item) for item in value]
        case dict():
            return {key: html_escape_json(value) for key, value in value.items()}
        case str():
            return escape(value)
        case _:
            # nothing to do, return unmodified
            return value
