from naming import safe_filename, chapter_label


def test_safe_filename_removes_illegal_chars():
    assert safe_filename('A/B:C*?"<>|D') == "ABCD"


def test_safe_filename_trims_whitespace():
    assert safe_filename("  Naruto  ") == "Naruto"


def test_chapter_label_integer_drops_decimal():
    assert chapter_label(1.0) == "1"


def test_chapter_label_decimal_kept():
    assert chapter_label(1.5) == "1.5"
