# Komiku Downloader

Download manga by title from [komiku.org](https://komiku.org/) and save each
chapter as a CBZ file for offline reading.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

## Usage

```powershell
.venv\Scripts\python komiku.py "naruto" --chapters 1-20
.venv\Scripts\python komiku.py "one piece" --chapters 5
.venv\Scripts\python komiku.py "naruto"            # all chapters
.venv\Scripts\python komiku.py "naruto" -o "E:\Manga" --delay 1
```

When several titles match your search, you'll get a numbered list to pick from.

**Choosing where to save:** if you don't pass `-o/--output`, a folder-picker
dialog opens so you can select the destination. Cancel it (or run on a machine
with no GUI) and it falls back to `~/Downloads/manga`. Pass `-o` to skip the
dialog entirely — useful for scripts.

### Flags

| Flag | Meaning |
|------|---------|
| `title` (positional) | Title to search for |
| `-c` / `--chapters` | `A-B` range, single `N`, or omit for all (decimals like `698.5` work) |
| `-o` / `--output` | Output root folder. If omitted, a folder picker opens (falls back to `~/Downloads/manga`) |
| `--delay` | Seconds between requests (default `0.5`) |
| `--force` | Re-download a chapter even if its `.cbz` already exists |

Files are saved to `<output>/<Title>/<Title> - Chapter <N>.cbz`. Each CBZ holds
the pages as zero-padded `001.jpg`, `002.jpg`, … so comic readers
(CDisplayEx, Tachiyomi, etc.) keep them in order. Chapters whose `.cbz` already
exists are skipped, so you can re-run to resume an interrupted batch.

## Tests

```powershell
.venv\Scripts\python -m pytest -v
```

The parser is covered by unit tests against saved HTML fixtures in
`tests/fixtures/` — no network access is needed to run the suite.

## How it works

1. Searches `api.komiku.org` (komiku's search endpoint) for the title.
2. Reads the series page to list every chapter (handles decimal chapters).
3. For each selected chapter, reads the reader page and collects the image URLs.
4. Downloads the images and zips them into a `.cbz`.

It is a plain HTTP client — it never opens a browser or runs page scripts, so it
does **not** trigger the pop-up/redirect ads you see when clicking around the
site in a browser. Requests are rate-limited (`--delay`) and sent with a normal
browser User-Agent to be polite to the site.

## Note

For personal, offline reading of content you are entitled to access.
