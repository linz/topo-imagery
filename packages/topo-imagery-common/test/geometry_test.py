from decimal import Decimal

import pytest
from pytest_subtests import SubTests
from topo_imagery_common.geometry import get_buffer_distance


def test_get_buffer_distance(subtests: SubTests) -> None:
    # Buffer factor of 2 decided in TDE-1049
    with subtests.test("0.1m gsd"):
        assert get_buffer_distance(Decimal("0.1")) == pytest.approx(0.000002)

    with subtests.test("1m gsd"):
        assert get_buffer_distance(Decimal("1")) == pytest.approx(0.00002)

    with subtests.test("10m gsd"):
        assert get_buffer_distance(Decimal("10")) == pytest.approx(0.0002)
