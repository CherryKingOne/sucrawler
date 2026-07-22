import html
import random
import re
import string


def strip_whitespace(text: str) -> str:
    return text.strip()


def strip_all_whitespace(text: str) -> str:
    return re.sub(r"\s+", "", text)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def html_escape(text: str) -> str:
    return html.escape(text)


def html_unescape(text: str) -> str:
    return html.unescape(text)


def random_string(length: int = 10, chars: str | None = None) -> str:
    if chars is None:
        chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def random_letters(length: int = 10) -> str:
    return random_string(length, string.ascii_letters)


def random_digits(length: int = 10) -> str:
    return random_string(length, string.digits)


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def snake_to_camel(text: str) -> str:
    components = text.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def camel_to_snake(text: str) -> str:
    result: list[str] = []
    for i, char in enumerate(text):
        if char.isupper() and i > 0:
            result.append("_")
        result.append(char.lower())
    return "".join(result)
