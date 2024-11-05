from random import choice, randint
from string import ascii_lowercase

import pytest


@pytest.fixture
def fake_linz_slug() -> str:
    random_string = "".join(choice(ascii_lowercase) for _ in range(6))
    start_year = randint(2000, 2009)
    end_year = randint(2010, 2019)
    gsd = choice([0.75, 0.3, 1, 0.075])

    return f"a-random-slug-{random_string}_{start_year}-{end_year}_{gsd}m"
