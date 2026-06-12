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
.venv\Scripts\python komiku.py "naruto" --chapters 1-20 -o "E:\Manga"
.venv\Scripts\python komiku.py "one piece" --chapters 5 -o "E:\Manga"
.venv\Scripts\python komiku.py "naruto" -o "E:\Manga"        # all chapters
.venv\Scripts\python komiku.py "kichiku eiyuu" --update -o "E:\Manga"  # only new
```

When several titles match your search, you'll get a numbered list to pick from.

**Choosing where to save (required):** you must always specify where manga is
saved. Either pass `-o/--output <folder>`, or omit it and pick a folder in the
dialog that opens. If you cancel the dialog (or run with no GUI and no `-o`), the
program prints an error and exits — there is no default location.

**Updating a series:** add `--update` (`-u`) to download only the chapters you
don't already have in the output folder:

```powershell
.venv\Scripts\python komiku.py "kichiku eiyuu" --update -o "E:\Manga"
```

It reports `Already up to date (...)` or `Found N new chapter(s): ...` and
fetches only the missing ones. `--update` ignores `--chapters`. A chapter whose
download is interrupted or incomplete is **not** saved as a `.cbz`, so a later
`--update` (or re-run) re-fetches it cleanly.

### Flags

| Flag | Meaning |
|------|---------|
| `title` (positional) | Title to search for |
| `-c` / `--chapters` | `A-B` range, single `N`, or omit for all (decimals like `698.5` work) |
| `-o` / `--output` | Output root folder (**required**) — pass it, or pick a folder in the dialog; no default |
| `-u` / `--update` | Download only chapters missing from the output folder (ignores `--chapters`) |
| `--delay` | Seconds between requests (default `0.5`) |
| `--force` | Re-download a chapter even if its `.cbz` already exists |

Files are saved to `<output>/<Title>/<Title> - Chapter <N>.cbz`. Each CBZ holds
the pages as zero-padded `001.jpg`, `002.jpg`, … so comic readers
(CDisplayEx, Tachiyomi, etc.) keep them in order. Chapters whose `.cbz` already
exists are skipped, so you can re-run (or use `--update`) to resume an
interrupted batch. A chapter is written only once **all** its pages download, so
partial chapters are never left behind.

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
