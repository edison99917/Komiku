import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from models import SearchResult, Chapter

BASE_URL = "https://komiku.org"

_MANGA_RE = re.compile(r"/manga/[^/]+/?$")


def parse_search(html):
    soup = BeautifulSoup(html, "html.parser")
    titles = {}
    order = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not _MANGA_RE.search(href):
            continue
        url = urljoin(BASE_URL, href)
        # Each result links twice: a thumbnail anchor (whose text is a genre
        # label like "Manga Aksi") and a title anchor carrying an <h3> with the
        # real series name. Prefer the <h3>.
        h3 = a.find("h3")
        title = h3.get_text(strip=True) if h3 else a.get_text(strip=True)
        if url not in titles:
            order.append(url)
            titles[url] = title
        elif h3 and title:
            titles[url] = title
    return [SearchResult(title=titles[u] or u, url=u) for u in order]


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
        chapters[num] = Chapter(number=num, url=urljoin(BASE_URL, a["href"]))
    return sorted(chapters.values(), key=lambda c: c.number)


def parse_series_title(html):
    soup = BeautifulSoup(html, "html.parser")
    og = soup.find("meta", attrs={"property": "og:title"})
    text = og.get("content", "").strip() if og and og.get("content") else ""
    if not text and soup.title and soup.title.string:
        # e.g. "Komik Naruto - Komiku" -> "Komik Naruto"
        text = soup.title.string.split(" - ")[0].strip()
    if not text:
        text = "Unknown"
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
