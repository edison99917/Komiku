from pathlib import Path

import komiku
from models import SearchResult


def test_choose_result_single_auto(monkeypatch):
    results = [SearchResult("Naruto", "https://komiku.org/manga/naruto/")]
    chosen = komiku.choose_result(results)
    assert chosen.url == "https://komiku.org/manga/naruto/"


def test_choose_result_multiple_uses_input(monkeypatch):
    results = [
        SearchResult("Naruto", "https://komiku.org/manga/naruto/"),
        SearchResult("Naruto Gaiden", "https://komiku.org/manga/naruto-gaiden/"),
    ]
    monkeypatch.setattr("builtins.input", lambda _: "2")
    chosen = komiku.choose_result(results)
    assert chosen.title == "Naruto Gaiden"


def test_default_output_dir_is_downloads_manga():
    p = komiku.default_output_dir()
    assert p.name == "manga"
    assert "Downloads" in str(p)


def test_slug_from_url():
    assert komiku._slug_from_url("https://komiku.org/manga/naruto/") == "naruto"
    assert komiku._slug_from_url("/manga/one-piece") == "one-piece"
    assert komiku._slug_from_url("https://komiku.org/") is None


def test_missing_integer_chapters_reports_gaps():
    present = {1.0, 1.5, 2.0, 4.0}
    # integers 3 is the only missing integer in [1, 4]; the missing 2.5 decimal
    # is intentionally not reported (we can't know which decimals should exist)
    assert komiku._missing_integer_chapters(1.0, 4.0, present) == [3.0]


def test_missing_integer_chapters_single_missing_chapter():
    # the single-chapter case (-c 5 when 5 doesn't exist) must still warn
    assert komiku._missing_integer_chapters(5.0, 5.0, {1.0, 2.0}) == [5.0]


def test_missing_integer_chapters_decimal_range_no_false_positive():
    assert komiku._missing_integer_chapters(1.5, 2.5, {1.5, 2.0, 2.5}) == []


def test_select_output_dir_returns_chosen(monkeypatch):
    monkeypatch.setattr(komiku, "_ask_directory", lambda d: "D:/Manga")
    assert komiku.select_output_dir() == Path("D:/Manga")


def test_select_output_dir_none_on_cancel(monkeypatch):
    monkeypatch.setattr(komiku, "_ask_directory", lambda d: "")
    assert komiku.select_output_dir() is None


def test_select_output_dir_none_when_picker_unavailable(monkeypatch):
    def boom(d):
        raise RuntimeError("no display")

    monkeypatch.setattr(komiku, "_ask_directory", boom)
    assert komiku.select_output_dir() is None


def test_main_errors_when_no_output_dir(monkeypatch, capsys):
    monkeypatch.setattr(komiku, "_ask_directory", lambda d: "")
    code = komiku.main(["naruto"])
    assert code == 2
    assert "output directory is required" in capsys.readouterr().out.lower()


import library
from models import Chapter


def test_select_chapters_update_returns_only_new(monkeypatch, tmp_path):
    all_ch = [Chapter(n, f"u{n}") for n in (1.0, 2.0, 3.0)]
    monkeypatch.setattr(library, "existing_chapter_numbers", lambda d: {1.0, 2.0})
    selected, msg = komiku.select_chapters(all_ch, chapters_spec=None,
                                            update=True, series_dir=tmp_path)
    assert [c.number for c in selected] == [3.0]
    assert "1 new" in msg


def test_select_chapters_update_up_to_date(monkeypatch, tmp_path):
    all_ch = [Chapter(n, f"u{n}") for n in (1.0, 2.0)]
    monkeypatch.setattr(library, "existing_chapter_numbers", lambda d: {1.0, 2.0})
    selected, msg = komiku.select_chapters(all_ch, chapters_spec=None,
                                            update=True, series_dir=tmp_path)
    assert selected == []
    assert "up to date" in msg.lower()


def test_select_chapters_update_no_existing_downloads_all(monkeypatch, tmp_path):
    all_ch = [Chapter(n, f"u{n}") for n in (1.0, 2.0)]
    monkeypatch.setattr(library, "existing_chapter_numbers", lambda d: set())
    selected, msg = komiku.select_chapters(all_ch, chapters_spec=None,
                                            update=True, series_dir=tmp_path)
    assert [c.number for c in selected] == [1.0, 2.0]
    assert "no existing download" in msg.lower()


def test_select_chapters_range_mode_unchanged(tmp_path):
    all_ch = [Chapter(n, f"u{n}") for n in (1.0, 2.0, 3.0)]
    selected, msg = komiku.select_chapters(all_ch, chapters_spec="1-2",
                                            update=False, series_dir=tmp_path)
    assert [c.number for c in selected] == [1.0, 2.0]
