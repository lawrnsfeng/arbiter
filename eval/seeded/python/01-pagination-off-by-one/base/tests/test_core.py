import pytest

from pager import total_pages


def test_total_pages_rounds_up():
    assert total_pages(10, 3) == 4


def test_total_pages_exact():
    assert total_pages(9, 3) == 3


def test_total_pages_rejects_zero():
    with pytest.raises(ValueError):
        total_pages(1, 0)
