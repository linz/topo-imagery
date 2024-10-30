import pytest

@pytest.fixture(autouse=True)
def fake_linz_slug() -> str:
    return "somewhere-in-new-zealand_2021-2023_0.75m"
