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


def _expected_missing(lo, hi, present):
    missing = []
    n = lo
    while n <= hi:
        if float(n) not in present:
            missing.append(float(n))
        n += 1
    return missing


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
        for n in _expected_missing(lo, hi, present):
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
