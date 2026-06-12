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


_CHAPTER_RE = re.compile(r"-chapter-([0-9]+(?:-[0-9]+)?)/?$")


def _chapter_number(href):
    m = _CHAPTER_RE.search(href)
    if not m:
        return None
    return float(m.group(1).replace("-", "."))


def parse_chapters(html):
    soup = BeautifulSoup(html, "html.parser")
    chapters = {}
    for a in soup.find_all("a", href=True):
        num = _chapter_number(a["href"])
        if num is None:
            continue
        chapters[num] = Chapter(number=num, url=a["href"])
    return sorted(chapters.values(), key=lambda c: c.number)


def parse_series_title(html):
    soup = BeautifulSoup(html, "html.parser")
    name = soup.find(itemprop="name")
    text = name.get_text(strip=True) if name else ""
    if not text:
        h1 = soup.find("h1")
        text = h1.get_text(strip=True) if h1 else "Unknown"
    return re.sub(r"^Komik\s+", "", text).strip()


def parse_images(html):
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if not src:
            continue
        if "img.komiku.org" in src:
            urls.append(src)
    return urls
