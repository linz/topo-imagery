from random import choice

from pytest import raises

from scripts.stac.util.linz_slug import SLUG_CHARS, slugify


def test_should_pass_through_output_alphabet_unchanged() -> None:
    assert slugify(SLUG_CHARS) == SLUG_CHARS


def test_should_pass_through_random_slug_unchanged() -> None:
    value = any_slug()
    assert slugify(slugify(value)) == slugify(value)


def test_should_lowercase_uppercase_ascii_characters() -> None:
    assert slugify("ABCDEFGHIJKLMNOPQRSTUVWXYZ") == "abcdefghijklmnopqrstuvwxyz"


def test_should_replace_spaces_with_hyphens() -> None:
    assert slugify("Upper North Island") == "upper-north-island"


def test_should_remove_apostrophes() -> None:
    assert slugify("Hawke's Bay") == "hawkes-bay"


def test_should_replace_slashes_with_hyphens() -> None:
    assert slugify("Tikitapu/Blue Lake") == "tikitapu-blue-lake"


def test_should_replace_commas_with_hyphens() -> None:
    assert slugify("Omere, Janus or Toby Rock") == "omere-janus-or-toby-rock"


def test_should_replace_ampersands_with_and() -> None:
    assert slugify("Gore A&P Showgrounds") == "gore-a-and-p-showgrounds"


def test_should_collapse_multiple_hyphens() -> None:
    assert slugify("Butlers 'V' Hut") == "butlers-v-hut"


def test_should_remove_diacritics() -> None:
    for value in ["á", "Á", "ä", "Ä", "ā", "Ā"]:
        assert slugify(value) == "a"
    for value in ["é", "É", "ē", "Ē"]:
        assert slugify(value) == "e"
    for value in ["ì", "Ì", "ī", "Ī"]:
        assert slugify(value) == "i"
    for value in ["ó", "Ó", "ô", "Ô", "ö", "Ö", "ō", "Ō"]:
        assert slugify(value) == "o"
    for value in ["ü", "Ü", "ū", "Ū"]:
        assert slugify(value) == "u"


def test_should_convert_o_slash_to_o() -> None:
    for value in ["ø", "Ø"]:
        assert slugify(value) == "o"


def test_should_handle_decomposed_characters() -> None:
    assert slugify("\u0041\u0304") == "a"


def test_should_treat_any_unhandled_characters_as_an_error() -> None:
    with raises(ValueError, match=r'Unhandled characters: "\\n", ";", "\\", "—", "“", "”"'):
        slugify("“a\\b//c—;\n”")


def any_slug() -> str:
    return "".join(choice(SLUG_CHARS) for _ in range(8))
