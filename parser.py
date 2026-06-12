import re

from bs4 import BeautifulSoup

from models import SearchResult, Chapter

_MANGA_RE = re.compile(r"/manga/[^/]+/?$")


def parse_search(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not _MANGA_RE.search(href):
            continue
        if href in seen:
            continue
        seen.add(href)
        title = a.get_text(strip=True) or href
        results.append(SearchResult(title=title, url=href))
    return results
