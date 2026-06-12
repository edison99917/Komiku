from pathlib import Path

from parser import parse_search

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_search_returns_series_links():
    results = parse_search(_load("search.html"))
    urls = [r.url for r in results]
    assert "https://komiku.org/manga/naruto/" in urls
    assert "https://komiku.org/manga/naruto-gaiden/" in urls
    assert all("/manga/" in r.url for r in results)


def test_parse_search_titles_and_dedup():
    results = parse_search(_load("search.html"))
    assert len(results) == 2
    assert results[0].title == "Naruto"


from parser import parse_chapters, parse_series_title


def test_parse_chapters_sorted_ascending_with_decimals():
    chapters = parse_chapters(_load("series.html"))
    numbers = [c.number for c in chapters]
    assert numbers == [1.0, 1.5, 2.0]
    assert chapters[0].url == "https://komiku.org/naruto-chapter-1/"


def test_parse_series_title_strips_komik_prefix():
    assert parse_series_title(_load("series.html")) == "Naruto"


def test_parse_search_prefers_h3_title_over_genre_label():
    # The thumbnail anchor's text is a genre label ("Manga Aksi"); the real
    # series name lives in the <h3> of the second anchor and must win.
    html = (
        '<a href="/manga/one-piece/"><img src="t.jpg">'
        '<div class="tpe1_inf"><b>Manga</b> Aksi</div></a>'
        '<a href="/manga/one-piece/"><h3>One Piece</h3></a>'
    )
    results = parse_search(html)
    assert len(results) == 1
    assert results[0].title == "One Piece"
    assert results[0].url == "https://komiku.org/manga/one-piece/"


def test_parse_series_title_falls_back_to_title_tag():
    html = "<head><title>Komik Bleach - Komiku</title></head><body></body>"
    assert parse_series_title(html) == "Bleach"


from parser import parse_images


def test_parse_images_only_reader_images_in_order():
    urls = parse_images(_load("chapter.html"))
    assert urls == [
        "https://img.komiku.org/wp-content/uploads/2267578-1.jpg",
        "https://img.komiku.org/wp-content/uploads/2267578-2.jpg",
        "https://img.komiku.org/wp-content/uploads/2267578-3.jpg",
    ]
    assert all("thumbnail.komiku.org" not in u for u in urls)
