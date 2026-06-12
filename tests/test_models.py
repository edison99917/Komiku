from models import SearchResult, Chapter


def test_search_result_fields():
    r = SearchResult(title="Naruto", url="https://komiku.org/manga/naruto/")
    assert r.title == "Naruto"
    assert r.url == "https://komiku.org/manga/naruto/"


def test_chapter_fields_and_ordering():
    a = Chapter(number=1.0, url="https://komiku.org/naruto-chapter-1/")
    b = Chapter(number=2.0, url="https://komiku.org/naruto-chapter-2/")
    assert a.number == 1.0
    assert sorted([b, a], key=lambda c: c.number)[0] is a
