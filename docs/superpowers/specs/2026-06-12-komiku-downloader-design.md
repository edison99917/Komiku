# Komiku Downloader — Design

**Date:** 2026-06-12
**Status:** Approved (pending spec review)

## Purpose

A command-line program that downloads manga by title from
[komiku.org](https://komiku.org/) and packages each chapter as a CBZ file for
offline reading. Intended for personal use.

## Decisions

| Decision | Choice |
|----------|--------|
| Language / runtime | Python 3 |
| HTTP + parsing | `requests` + `BeautifulSoup` (bs4) |
| Output format | CBZ (one archive per chapter) |
| Interface | CLI, title as argument |
| Scope per run | Chapter range (also supports single / all) |
| Save location | Windows `Downloads\manga\<Title>\` (override with `--output`) |
| Multiple matches | Interactive numbered pick |
| Tests | Yes — parser unit tests against saved HTML fixtures (TDD) |

## How komiku.org works (verified 2026-06-12)

- **Search:** `GET https://komiku.org/?s=<title>` returns an HTML results page.
  Series are linked via anchors whose `href` matches `/manga/<slug>/`.
- **Series page** (`/manga/<slug>/`): contains the series title, a cover image,
  and a list of chapter links matching `/<slug>-chapter-<num>/`. Chapter numbers
  may be decimals (e.g. `698-5` → 698.5).
- **Chapter page** (`/<slug>-chapter-<num>/`): the reader images are plain
  `<img>` tags (no JS lazy-loading) hosted on `img.komiku.org`
  (e.g. `https://img.komiku.org/wp-content/uploads/2267578-1.jpg`), in page order.

Because images are present in the static HTML, a plain HTTP client is sufficient
— no headless browser needed.

## Usage

```
python komiku.py "naruto" --chapters 1-20      # range
python komiku.py "one piece" --chapters 5      # single chapter
python komiku.py "naruto"                       # prompts; defaults to all
python komiku.py "naruto" --chapters 1-20 --output "E:\Manga"
```

CLI flags:
- positional `title` — search query (required)
- `--chapters` / `-c` — range `A-B`, single `N`, or omitted (all). Accepts decimals.
- `--output` / `-o` — destination root (default: `~/Downloads/manga`)
- `--delay` — seconds between requests (default: small polite delay)

## Flow

1. **Search** — `?s=<title>`; collect `/manga/<slug>/` links + titles.
   - 0 results → friendly error and exit.
   - 1 result → use it.
   - many → print a numbered list; user types the number.
2. **Chapter list** — GET the series page; extract `(number, url)` for every
   `/<slug>-chapter-<num>/` link; sort ascending; filter to the requested range.
   Warn about any requested numbers that don't exist.
3. **Download** — for each selected chapter: GET the chapter page, collect the
   ordered `img.komiku.org` image URLs, download each with a realistic
   `User-Agent` + `Referer`, retry on failure, and pause `--delay` between requests.
4. **Package** — write images into a temp area named `001.jpg`, `002.jpg`, …
   (zero-padded to preserve reader order), then zip into
   `<output>/<Title>/<Title> - Chapter <N>.cbz`.

## Architecture

A single small package; each module has one clear job and the parsing logic is
pure (no network) so it can be unit-tested against fixtures.

- `komiku.py` — CLI entry point: argument parsing, orchestration, user prompts.
- `client.py` — a configured `requests.Session`: headers, retry/backoff,
  rate-limit (delay) wrapper. The one place that touches the network.
- `parser.py` — **pure functions**, input = HTML string, output = data:
  - `parse_search(html) -> list[SearchResult(title, url)]`
  - `parse_chapters(html, slug) -> list[Chapter(number, url)]`
  - `parse_images(html) -> list[str]` (ordered image URLs)
  - `parse_series_title(html) -> str`
- `downloader.py` — given a chapter's image URLs, download bytes (via `client`)
  and build the `.cbz`.
- `models.py` — small dataclasses: `SearchResult`, `Chapter`.

## Error handling

- **Network errors:** retry 3× with backoff. After exhausting retries on an
  *image*, skip that image with a warning rather than aborting the whole run.
- **Empty chapter** (zero images parsed): warn and continue to the next chapter.
- **Out-of-range chapters:** warn which requested numbers were not found.
- **Resume:** if a chapter's `.cbz` already exists, skip it (unless `--force`).
- **No matches / no internet:** clear message, non-zero exit code.

## Testing

- `parser.py` is covered by unit tests using a handful of saved HTML fixtures
  (`tests/fixtures/`): a search page, a series page, a chapter page. No live
  network in the test suite.
- A small smoke test for range parsing (`"1-20"`, `"5"`, decimals).

## Dependencies

`requests`, `beautifulsoup4`. Pinned in `requirements.txt`. Tests use `pytest`.

## Out of scope (YAGNI)

- GUI / web interface
- Auto-update / watch for new chapters
- Formats other than CBZ (PDF/folders)
- Parallel/threaded downloads (sequential keeps it polite and simple; can add later)

## Legal note

For personal, offline reading of content the user is entitled to access. The
tool sends a realistic User-Agent and rate-limits requests to avoid burdening
the site.
