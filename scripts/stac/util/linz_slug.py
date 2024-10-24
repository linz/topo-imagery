from json import dumps
from re import findall, sub
from unicodedata import normalize

from scripts.stac.imagery.metadata_constants import CollectionMetadata

SLUG_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789_.-"


def slugify(value: str) -> str:
    """
    Function to convert a string to a slugified string.
    Slugified in this context means:
        - Only SLUG_CHARS are permitted
        - ASCII upper case characters converted to lower case characters
        - Some special characters converted to a similar ASCII representation, for example: & -> -and-; ø -> o
        - Multiple hyphens collapsed into one hyphen

    Args:
        value: string to be converted to slug

    Returns:
        converted string, processed according to the above rules

    """
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
    """
    Function to remove diacritics from a string.
    Args:
        value: input string

    Returns:
        converted string, with diacritics replaced by their respective ASCII base character without diacritics
    """
    combining_diacritical_marks = r"[\u0300-\u036F]"
    return sub(combining_diacritical_marks, "", normalize("NFD", value))


def create_linz_slug(metadata: CollectionMetadata) -> str:
    """
    Function to create a linz-slugified string based on a collection's metadata dictionary.
    Args:
        metadata: Collection metadata dictionary

    Returns:
        string built from the collection's metadata dictionary in the following format:
        Imagery:      [<geographic_description>|<region>][_<survey_number>?]_<start_year>[-<end_year>?]_<gsd>m
        Elevation:    [<geographic_description>|<region>]_<start_year>[-<end_year>?]
    """

    slug_items = [
        metadata["geographic_description"] or metadata["region"],
    ]
    if metadata["historic_survey_number"]:
        slug_items.append("historic_survey_number")
    slug_items.append(
        f"{metadata["start_datetime"].year}{-metadata["end_datetime"].year if
        metadata["end_datetime"].year > metadata["start_datetime"].year else ""}"
    )
    if metadata["category"] not in ["dem", "dsm"]:
        slug_items.append(f"{metadata['gsd']}m")

    raw_slug = "_".join(slug_items)

    return slugify(raw_slug)
