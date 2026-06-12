from library import existing_chapter_numbers


def test_existing_chapter_numbers_parses_integers_and_decimals(tmp_path):
    (tmp_path / "Naruto - Chapter 1.cbz").write_bytes(b"x")
    (tmp_path / "Naruto - Chapter 8.5.cbz").write_bytes(b"x")
    (tmp_path / "Naruto - Chapter 10.cbz").write_bytes(b"x")
    (tmp_path / "notes.txt").write_text("ignore me")
    assert existing_chapter_numbers(tmp_path) == {1.0, 8.5, 10.0}


def test_existing_chapter_numbers_missing_dir_is_empty(tmp_path):
    assert existing_chapter_numbers(tmp_path / "does-not-exist") == set()


from library import new_chapters
from models import Chapter


def test_new_chapters_filters_present_preserving_order():
    chapters = [Chapter(n, f"u{n}") for n in (1.0, 2.0, 2.5, 3.0)]
    result = new_chapters(chapters, {1.0, 2.0})
    assert [c.number for c in result] == [2.5, 3.0]


def test_new_chapters_empty_when_all_present():
    chapters = [Chapter(n, f"u{n}") for n in (1.0, 2.0)]
    assert new_chapters(chapters, {1.0, 2.0}) == []
