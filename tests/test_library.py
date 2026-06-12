from library import existing_chapter_numbers


def test_existing_chapter_numbers_parses_integers_and_decimals(tmp_path):
    (tmp_path / "Naruto - Chapter 1.cbz").write_bytes(b"x")
    (tmp_path / "Naruto - Chapter 8.5.cbz").write_bytes(b"x")
    (tmp_path / "Naruto - Chapter 10.cbz").write_bytes(b"x")
    (tmp_path / "notes.txt").write_text("ignore me")
    assert existing_chapter_numbers(tmp_path) == {1.0, 8.5, 10.0}


def test_existing_chapter_numbers_missing_dir_is_empty(tmp_path):
    assert existing_chapter_numbers(tmp_path / "does-not-exist") == set()
