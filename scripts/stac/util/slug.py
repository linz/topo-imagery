from json import dumps
from re import findall, sub
from unicodedata import normalize

SLUG_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789_.-"


def slugify(value: str) -> str:
    result = sub(
        r"--+",
        "-",
        sub(
            r"[ ,/]",
            "-",
            remove_diacritics(value).replace("'", "").replace("ø", "o").replace("Ø", "O").replace("&", "-and-").lower(),
        ),
    )

    unhandled_characters = findall(f"[^{SLUG_CHARS}]", result)
    if unhandled_characters:
        sorted_unique_characters = sorted(set(unhandled_characters))
        formatted_characters = [
            dumps(character, ensure_ascii=False).replace("\\\\", "\\") for character in sorted_unique_characters
        ]
        raise ValueError(f"Unhandled characters: {', '.join(formatted_characters)}")

    return result


def remove_diacritics(value: str) -> str:
    combining_diacritical_marks = r"[\u0300-\u036F]"
    return sub(combining_diacritical_marks, "", normalize("NFD", value))
