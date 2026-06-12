import argparse
import math
import re
import sys
from pathlib import Path
from urllib.parse import quote_plus

from client import make_session, get
from downloader import build_cbz, download_images
from naming import safe_filename, chapter_label
from parser import parse_search, parse_chapters, parse_images, parse_series_title
from ranges import parse_range, filter_chapters

# komiku.org renders search results client-side; the actual results are served
# as an HTML fragment from this endpoint.
SEARCH_URL = "https://api.komiku.org/?post_type=manga&s={query}"


def default_output_dir():
    return Path.home() / "Downloads" / "manga"


def _ask_directory(initialdir):
    """Open a native folder-picker dialog and return the chosen path string
    ("" if cancelled). Raises if tkinter / a display is unavailable."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        return filedialog.askdirectory(
            title="Choose where to save manga", initialdir=str(initialdir)
        )
    finally:
        root.destroy()


def select_output_dir(default):
    """Let the user pick a save folder via a graphical dialog. Falls back to
    `default` if the dialog is cancelled or no GUI is available."""
    try:
        chosen = _ask_directory(default)
    except Exception as exc:
        print(f"(Folder picker unavailable: {exc}; using {default})")
        return Path(default)
    if not chosen:
        print(f"(No folder selected; using {default})")
        return Path(default)
    return Path(chosen)


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


def _slug_from_url(url):
    m = re.search(r"/manga/([^/]+)/?$", url)
    return m.group(1) if m else None


def _missing_integer_chapters(lo, hi, present):
    """Integer chapter numbers within [lo, hi] that the series doesn't have."""
    return [float(n) for n in range(math.ceil(lo), math.floor(hi) + 1)
            if float(n) not in present]


def run(title, chapters_spec, output_root, delay, force):
    session = make_session()

    print(f"Searching for {title!r} ...")
    search_html = get(session, SEARCH_URL.format(query=quote_plus(title)), delay=delay).text
    results = parse_search(search_html)
    chosen = choose_result(results)
    if chosen is None:
        print("No matches found.")
        return 1

    series_html = get(session, chosen.url, delay=delay).text
    series_title = parse_series_title(series_html)
    all_chapters = parse_chapters(series_html, _slug_from_url(chosen.url))
    if not all_chapters:
        print("No chapters found on the series page.")
        return 1

    lo, hi = parse_range(chapters_spec)
    selected = filter_chapters(all_chapters, lo, hi)

    if lo is not None:
        present = {c.number for c in all_chapters}
        for n in _missing_integer_chapters(lo, hi, present):
            print(f"  ! chapter {chapter_label(n)} not available, skipping")

    if not selected:
        print("No chapters matched the requested range.")
        return 1

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


def main(argv=None):
    # Manga titles often contain non-ASCII punctuation; avoid UnicodeEncodeError
    # when printing to a legacy (cp1252) Windows console.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    parser = argparse.ArgumentParser(description="Download manga from komiku.org as CBZ.")
    parser.add_argument("title", help="manga title to search for")
    parser.add_argument("-c", "--chapters", default=None,
                        help="chapter range, e.g. '1-20', '5', or omit for all")
    parser.add_argument("-o", "--output", default=None,
                        help="output root folder; if omitted, a folder picker "
                             "opens (default: ~/Downloads/manga)")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="seconds between requests (default 0.5)")
    parser.add_argument("--force", action="store_true",
                        help="re-download chapters even if the .cbz exists")
    args = parser.parse_args(argv)

    if args.output:
        output_root = Path(args.output)
    else:
        output_root = select_output_dir(default_output_dir())
    try:
        return run(args.title, args.chapters, output_root, args.delay, args.force)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
