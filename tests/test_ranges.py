import pytest

from ranges import parse_range, filter_chapters
from models import Chapter


def test_parse_range_single():
    lo, hi = parse_range("5")
    assert (lo, hi) == (5.0, 5.0)


def test_parse_range_span():
    lo, hi = parse_range("1-20")
    assert (lo, hi) == (1.0, 20.0)


def test_parse_range_none_is_all():
    assert parse_range(None) == (None, None)


def test_parse_range_invalid_raises():
    with pytest.raises(ValueError):
        parse_range("abc")


def test_filter_chapters_inclusive():
    chapters = [Chapter(n, f"u{n}") for n in (1.0, 1.5, 2.0, 3.0)]
    selected = filter_chapters(chapters, 1.0, 2.0)
    assert [c.number for c in selected] == [1.0, 1.5, 2.0]


def test_filter_chapters_all_when_none():
    chapters = [Chapter(n, f"u{n}") for n in (1.0, 2.0)]
    assert filter_chapters(chapters, None, None) == chapters
