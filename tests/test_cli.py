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
