# Komiku Downloader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Python CLI that downloads manga by title from komiku.org and packages each chapter as a CBZ file.

**Architecture:** A small package with pure parsing functions (`parser.py`) testable against saved HTML fixtures, a network layer (`client.py`) wrapping a `requests.Session` with headers/retry/delay, a `downloader.py` that fetches images and zips CBZ files, and a `komiku.py` CLI that orchestrates search → chapter-selection → download.

**Tech Stack:** Python 3, `requests`, `beautifulsoup4`, `pytest`.

---

## File Structure

- `requirements.txt` — runtime + test dependencies
- `models.py` — dataclasses `SearchResult`, `Chapter`
- `parser.py` — pure HTML parsing functions
- `client.py` — configured `requests.Session` (headers, retry, delay)
- `downloader.py` — download images + build CBZ
- `komiku.py` — CLI entry point / orchestration
- `tests/fixtures/` — saved HTML samples (`search.html`, `series.html`, `chapter.html`)
- `tests/test_parser.py` — parser unit tests
- `tests/test_ranges.py` — chapter-range parsing tests

---

### Task 1: Project scaffold and dependencies

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `tests/__init__.py` (empty)

- [ ] **Step 1: Write `requirements.txt`**

```
requests==2.32.3
beautifulsoup4==4.12.3
pytest==8.3.3
```

- [ ] **Step 2: Write `.gitignore`**

```
__pycache__/
*.pyc
.venv/
venv/
manga/
*.cbz
.pytest_cache/
```

- [ ] **Step 3: Create empty `tests/__init__.py`**

(empty file)

- [ ] **Step 4: Create venv and install**

Run:
```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```
Expected: installs requests, beautifulsoup4, pytest with no errors.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .gitignore tests/__init__.py
git commit -m "chore: project scaffold and dependencies"
```

---

### Task 2: Data models

**Files:**
- Create: `models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'models'`

- [ ] **Step 3: Write minimal implementation**

```python
# models.py
from dataclasses import dataclass


@dataclass
class SearchResult:
    title: str
    url: str


@dataclass
class Chapter:
    number: float
    url: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_models.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add models.py tests/test_models.py
git commit -m "feat: add SearchResult and Chapter models"
```

---

### Task 3: Save HTML fixtures

**Files:**
- Create: `tests/fixtures/search.html`
- Create: `tests/fixtures/series.html`
- Create: `tests/fixtures/chapter.html`

- [ ] **Step 1: Create `tests/fixtures/search.html`**

A minimal but representative search results page. The parser must extract anchors whose href matches `/manga/<slug>/`.

```html
<!DOCTYPE html>
<html><body>
<div class="daftar">
  <div class="bge">
    <a href="https://komiku.org/manga/naruto/" class="bgei">
      <h3>Naruto</h3>
    </a>
  </div>
  <div class="bge">
    <a href="https://komiku.org/manga/naruto-gaiden/" class="bgei">
      <h3>Naruto Gaiden</h3>
    </a>
  </div>
</div>
<a href="https://komiku.org/genre/action/">Action</a>
</body></html>
```

- [ ] **Step 2: Create `tests/fixtures/series.html`**

A minimal series page with title, cover, and chapter links matching `/<slug>-chapter-<num>/`, including a decimal chapter.

```html
<!DOCTYPE html>
<html><body>
<h1 id="Judul"><span itemprop="name">Komik Naruto</span></h1>
<div class="ims"><img src="https://thumbnail.komiku.org/uploads/manga/naruto/cover.jpg"></div>
<table id="Daftar_Chapter">
  <tr><td><a href="https://komiku.org/naruto-chapter-2/">Chapter 2</a></td><td>22/08/2020</td></tr>
  <tr><td><a href="https://komiku.org/naruto-chapter-1-5/">Chapter 1.5</a></td><td>22/08/2020</td></tr>
  <tr><td><a href="https://komiku.org/naruto-chapter-1/">Chapter 1</a></td><td>22/08/2020</td></tr>
</table>
</body></html>
```

- [ ] **Step 3: Create `tests/fixtures/chapter.html`**

A minimal chapter page with reader images on `img.komiku.org` plus a decoy thumbnail image that must NOT be collected.

```html
<!DOCTYPE html>
<html><body>
<img src="https://thumbnail.komiku.org/uploads/manga/naruto/cover.jpg" alt="cover">
<div id="Baca_Komik">
  <img src="https://img.komiku.org/wp-content/uploads/2267578-1.jpg">
  <img src="https://img.komiku.org/wp-content/uploads/2267578-2.jpg">
  <img src="https://img.komiku.org/wp-content/uploads/2267578-3.jpg">
</div>
</body></html>
```

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/
git commit -m "test: add HTML fixtures for parser tests"
```

---

### Task 4: Parse search results

**Files:**
- Create: `parser.py`
- Test: `tests/test_parser.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_parser.py
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
    # genre/non-series links excluded
    assert all("/manga/" in r.url for r in results)


def test_parse_search_titles_and_dedup():
    results = parse_search(_load("search.html"))
    assert len(results) == 2
    assert results[0].title == "Naruto"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_parser.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'parser'` (or ImportError for `parse_search`)

- [ ] **Step 3: Write minimal implementation**

```python
# parser.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_parser.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add parser.py tests/test_parser.py
git commit -m "feat: parse search results into SearchResult list"
```

---

### Task 5: Parse chapter list and series title

**Files:**
- Modify: `parser.py`
- Modify: `tests/test_parser.py`

- [ ] **Step 1: Write the failing test (append to `tests/test_parser.py`)**

```python
from parser import parse_chapters, parse_series_title


def test_parse_chapters_sorted_ascending_with_decimals():
    chapters = parse_chapters(_load("series.html"))
    numbers = [c.number for c in chapters]
    assert numbers == [1.0, 1.5, 2.0]
    assert chapters[0].url == "https://komiku.org/naruto-chapter-1/"


def test_parse_series_title_strips_komik_prefix():
    assert parse_series_title(_load("series.html")) == "Naruto"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_parser.py -v`
Expected: FAIL with ImportError for `parse_chapters` / `parse_series_title`

- [ ] **Step 3: Write minimal implementation (append to `parser.py`)**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_parser.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add parser.py tests/test_parser.py
git commit -m "feat: parse chapter list and series title"
```

---

### Task 6: Parse chapter images

**Files:**
- Modify: `parser.py`
- Modify: `tests/test_parser.py`

- [ ] **Step 1: Write the failing test (append to `tests/test_parser.py`)**

```python
from parser import parse_images


def test_parse_images_only_reader_images_in_order():
    urls = parse_images(_load("chapter.html"))
    assert urls == [
        "https://img.komiku.org/wp-content/uploads/2267578-1.jpg",
        "https://img.komiku.org/wp-content/uploads/2267578-2.jpg",
        "https://img.komiku.org/wp-content/uploads/2267578-3.jpg",
    ]
    # thumbnail/cover excluded
    assert all("thumbnail.komiku.org" not in u for u in urls)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_parser.py -v`
Expected: FAIL with ImportError for `parse_images`

- [ ] **Step 3: Write minimal implementation (append to `parser.py`)**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_parser.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add parser.py tests/test_parser.py
git commit -m "feat: parse reader image urls from chapter page"
```

---

### Task 7: Chapter range parsing

**Files:**
- Create: `ranges.py`
- Test: `tests/test_ranges.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ranges.py
import pytest

from ranges import parse_range, filter_chapters
from models import Chapter


def test_parse_range_single():
    lo, hi = parse_range("5")
    assert (lo, hi) == (5.0, 5.0)


def test_parse_range_span():
    lo, hi = parse_range("1-20")
    assert (lo, hi) == (1.0, 20.0)


def test_parse_range_none_is_all():
    assert parse_range(None) == (None, None)


def test_parse_range_invalid_raises():
    with pytest.raises(ValueError):
        parse_range("abc")


def test_filter_chapters_inclusive():
    chapters = [Chapter(n, f"u{n}") for n in (1.0, 1.5, 2.0, 3.0)]
    selected = filter_chapters(chapters, 1.0, 2.0)
    assert [c.number for c in selected] == [1.0, 1.5, 2.0]


def test_filter_chapters_all_when_none():
    chapters = [Chapter(n, f"u{n}") for n in (1.0, 2.0)]
    assert filter_chapters(chapters, None, None) == chapters
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_ranges.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ranges'`

- [ ] **Step 3: Write minimal implementation**

```python
# ranges.py
def parse_range(spec):
    if spec is None:
        return (None, None)
    spec = spec.strip()
    try:
        if "-" in spec:
            lo_s, hi_s = spec.split("-", 1)
            return (float(lo_s), float(hi_s))
        v = float(spec)
        return (v, v)
    except ValueError:
        raise ValueError(f"Invalid chapter range: {spec!r}")


def filter_chapters(chapters, lo, hi):
    if lo is None and hi is None:
        return chapters
    return [c for c in chapters if lo <= c.number <= hi]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_ranges.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add ranges.py tests/test_ranges.py
git commit -m "feat: chapter range parsing and filtering"
```

---

### Task 8: HTTP client

**Files:**
- Create: `client.py`
- Test: `tests/test_client.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_client.py
from client import make_session, DEFAULT_HEADERS


def test_make_session_sets_user_agent_and_referer():
    s = make_session()
    assert "User-Agent" in s.headers
    assert "komiku" in s.headers["Referer"]


def test_default_headers_has_realistic_user_agent():
    assert "Mozilla" in DEFAULT_HEADERS["User-Agent"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_client.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'client'`

- [ ] **Step 3: Write minimal implementation**

```python
# client.py
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Referer": "https://komiku.org/",
}


def make_session():
    s = requests.Session()
    s.headers.update(DEFAULT_HEADERS)
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def get(session, url, delay=0.0):
    if delay:
        time.sleep(delay)
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_client.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add client.py tests/test_client.py
git commit -m "feat: requests session with headers and retry"
```

---

### Task 9: Downloader and CBZ packaging

**Files:**
- Create: `downloader.py`
- Test: `tests/test_downloader.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_downloader.py
import zipfile
from pathlib import Path

from downloader import build_cbz


def test_build_cbz_writes_padded_ordered_images(tmp_path):
    images = [b"img-a", b"img-b", b"img-c"]
    out = tmp_path / "Naruto - Chapter 1.cbz"
    build_cbz(images, out)
    assert out.exists()
    with zipfile.ZipFile(out) as zf:
        names = sorted(zf.namelist())
        assert names == ["001.jpg", "002.jpg", "003.jpg"]
        assert zf.read("001.jpg") == b"img-a"
        assert zf.read("003.jpg") == b"img-c"


def test_build_cbz_creates_parent_dirs(tmp_path):
    out = tmp_path / "Naruto" / "Naruto - Chapter 1.cbz"
    build_cbz([b"x"], out)
    assert out.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_downloader.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'downloader'`

- [ ] **Step 3: Write minimal implementation**

```python
# downloader.py
import zipfile
from pathlib import Path

from client import get


def build_cbz(images, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_STORED) as zf:
        for i, data in enumerate(images, start=1):
            zf.writestr(f"{i:03d}.jpg", data)


def download_images(session, urls, delay=0.0):
    images = []
    for idx, url in enumerate(urls, start=1):
        try:
            resp = get(session, url, delay=delay)
            images.append(resp.content)
        except Exception as exc:
            print(f"  ! skipped image {idx} ({url}): {exc}")
    return images
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_downloader.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add downloader.py tests/test_downloader.py
git commit -m "feat: download images and build cbz archives"
```

---

### Task 10: Filename sanitization helper

**Files:**
- Create: `naming.py`
- Test: `tests/test_naming.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_naming.py
from naming import safe_filename, chapter_label


def test_safe_filename_removes_illegal_chars():
    assert safe_filename('A/B:C*?"<>|D') == "ABCD"


def test_safe_filename_trims_whitespace():
    assert safe_filename("  Naruto  ") == "Naruto"


def test_chapter_label_integer_drops_decimal():
    assert chapter_label(1.0) == "1"


def test_chapter_label_decimal_kept():
    assert chapter_label(1.5) == "1.5"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_naming.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'naming'`

- [ ] **Step 3: Write minimal implementation**

```python
# naming.py
import re

_ILLEGAL = re.compile(r'[\\/:*?"<>|]')


def safe_filename(name):
    return _ILLEGAL.sub("", name).strip()


def chapter_label(number):
    if number == int(number):
        return str(int(number))
    return str(number)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_naming.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add naming.py tests/test_naming.py
git commit -m "feat: filename sanitization and chapter labels"
```

---

### Task 11: CLI orchestration

**Files:**
- Create: `komiku.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'komiku'` (or AttributeError)

- [ ] **Step 3: Write minimal implementation**

```python
# komiku.py
import argparse
import sys
from pathlib import Path

from client import make_session, get
from downloader import build_cbz, download_images
from naming import safe_filename, chapter_label
from parser import parse_search, parse_chapters, parse_images, parse_series_title
from ranges import parse_range, filter_chapters

SEARCH_URL = "https://komiku.org/?s={query}"


def default_output_dir():
    return Path.home() / "Downloads" / "manga"


def choose_result(results):
    if not results:
        return None
    if len(results) == 1:
        return results[0]
    print("Multiple matches found:")
    for i, r in enumerate(results, start=1):
        print(f"  {i}. {r.title}  ({r.url})")
    while True:
        choice = input("Pick a number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(results):
            return results[int(choice) - 1]
        print("Invalid choice, try again.")


def run(title, chapters_spec, output_root, delay, force):
    session = make_session()

    print(f"Searching for {title!r} ...")
    search_html = get(session, SEARCH_URL.format(query=title), delay=delay).text
    results = parse_search(search_html)
    chosen = choose_result(results)
    if chosen is None:
        print("No matches found.")
        return 1

    series_html = get(session, chosen.url, delay=delay).text
    series_title = parse_series_title(series_html)
    all_chapters = parse_chapters(series_html)
    if not all_chapters:
        print("No chapters found on the series page.")
        return 1

    lo, hi = parse_range(chapters_spec)
    selected = filter_chapters(all_chapters, lo, hi)
    if not selected:
        print("No chapters matched the requested range.")
        return 1

    if lo is not None:
        present = {c.number for c in all_chapters}
        requested = {c.number for c in selected}
        missing = sorted(n for n in (present | requested) if lo <= n <= hi) and [
            n for n in _expected_missing(lo, hi, present)
        ]
        for n in missing:
            print(f"  ! chapter {chapter_label(n)} not available, skipping")

    series_dir = Path(output_root) / safe_filename(series_title)
    print(f"Downloading {len(selected)} chapter(s) of {series_title!r} to {series_dir}")

    for ch in selected:
        label = chapter_label(ch.number)
        out_path = series_dir / f"{safe_filename(series_title)} - Chapter {label}.cbz"
        if out_path.exists() and not force:
            print(f"  = Chapter {label} already exists, skipping")
            continue
        print(f"  > Chapter {label}")
        chapter_html = get(session, ch.url, delay=delay).text
        image_urls = parse_images(chapter_html)
        if not image_urls:
            print(f"  ! Chapter {label} had no images, skipping")
            continue
        images = download_images(session, image_urls, delay=delay)
        if not images:
            print(f"  ! Chapter {label} downloaded zero images, skipping")
            continue
        build_cbz(images, out_path)
        print(f"    saved {out_path.name} ({len(images)} pages)")

    print("Done.")
    return 0


def _expected_missing(lo, hi, present):
    missing = []
    n = lo
    while n <= hi:
        if float(n) not in present:
            missing.append(float(n))
        n += 1
    return missing


def main(argv=None):
    parser = argparse.ArgumentParser(description="Download manga from komiku.org as CBZ.")
    parser.add_argument("title", help="manga title to search for")
    parser.add_argument("-c", "--chapters", default=None,
                        help="chapter range, e.g. '1-20', '5', or omit for all")
    parser.add_argument("-o", "--output", default=None,
                        help="output root folder (default: ~/Downloads/manga)")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="seconds between requests (default 0.5)")
    parser.add_argument("--force", action="store_true",
                        help="re-download chapters even if the .cbz exists")
    args = parser.parse_args(argv)

    output_root = Path(args.output) if args.output else default_output_dir()
    try:
        return run(args.title, args.chapters, output_root, args.delay, args.force)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_cli.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Simplify the missing-chapter logic**

The `missing` computation in `run()` is convoluted. Replace the block:

```python
    if lo is not None:
        present = {c.number for c in all_chapters}
        requested = {c.number for c in selected}
        missing = sorted(n for n in (present | requested) if lo <= n <= hi) and [
            n for n in _expected_missing(lo, hi, present)
        ]
        for n in missing:
            print(f"  ! chapter {chapter_label(n)} not available, skipping")
```

with:

```python
    if lo is not None:
        present = {c.number for c in all_chapters}
        for n in _expected_missing(lo, hi, present):
            print(f"  ! chapter {chapter_label(n)} not available, skipping")
```

- [ ] **Step 6: Run the full test suite**

Run: `.venv/Scripts/python -m pytest -v`
Expected: PASS (all tests across all files)

- [ ] **Step 7: Commit**

```bash
git add komiku.py tests/test_cli.py
git commit -m "feat: CLI orchestration for search, select, download"
```

---

### Task 12: README and live smoke test

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# Komiku Downloader

Download manga by title from [komiku.org](https://komiku.org/) and save each
chapter as a CBZ file.

## Setup

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

## Usage

```bash
.venv/Scripts/python komiku.py "naruto" --chapters 1-20
.venv/Scripts/python komiku.py "one piece" --chapters 5
.venv/Scripts/python komiku.py "naruto"          # all chapters
.venv/Scripts/python komiku.py "naruto" -o "E:\Manga" --delay 1
```

Flags:
- `-c/--chapters` — `A-B`, single `N`, or omit for all (decimals supported)
- `-o/--output` — output root (default `~/Downloads/manga`)
- `--delay` — seconds between requests (default 0.5)
- `--force` — re-download even if the `.cbz` already exists

Files are saved to `<output>/<Title>/<Title> - Chapter <N>.cbz`.

## Tests

```bash
.venv/Scripts/python -m pytest -v
```

## Note

For personal, offline reading. The tool rate-limits requests to be polite to the site.
```

- [ ] **Step 2: Live smoke test (one short chapter)**

Run:
```bash
.venv/Scripts/python komiku.py "naruto" --chapters 1 --delay 1
```
Expected: prints search → selects/asks → downloads Chapter 1 → writes a `.cbz`
under `~/Downloads/manga/Naruto/`. Open the `.cbz` (it's a zip) to confirm it
contains ordered `001.jpg`, `002.jpg`, … images.

If parsing fails against the live site, capture the live HTML into
`tests/fixtures/` and adjust the relevant `parser.py` function + its test.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README and usage"
```

---

## Self-Review Notes

- **Spec coverage:** search (Task 4), chapter list + title (Task 5), images (Task 6),
  range parsing/filtering (Task 7), client w/ headers+retry+delay (Task 8), CBZ +
  download-with-skip (Task 9), filename/label safety (Task 10), CLI w/ interactive
  pick + Downloads default + resume/--force (Task 11), README + live verification (Task 12).
- **Resume behavior:** existing `.cbz` skipped unless `--force` (Task 11) — matches spec.
- **Decimal chapters:** handled in `_chapter_number` (Task 5), `chapter_label` (Task 10),
  range filter (Task 7).
- **Names consistent across tasks:** `make_session`, `get`, `build_cbz`, `download_images`,
  `parse_search`, `parse_chapters`, `parse_series_title`, `parse_images`, `parse_range`,
  `filter_chapters`, `safe_filename`, `chapter_label`, `choose_result`, `default_output_dir`.
```
