import re
from pathlib import Path

_CBZ_RE = re.compile(r"Chapter\s+([0-9]+(?:\.[0-9]+)?)\.cbz$", re.IGNORECASE)


def existing_chapter_numbers(series_dir):
    """Chapter numbers already downloaded, read from .cbz filenames in
    series_dir. Returns an empty set if the directory does not exist."""
    numbers = set()
    directory = Path(series_dir)
    if not directory.is_dir():
        return numbers
    for path in directory.glob("*.cbz"):
        match = _CBZ_RE.search(path.name)
        if match:
            numbers.add(float(match.group(1)))
    return numbers


def new_chapters(chapters, existing_numbers):
    """Chapters whose number is not already downloaded, order preserved."""
    return [c for c in chapters if c.number not in existing_numbers]
