# Update Mode, Required Output Dir & Download Robustness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an `--update` mode that downloads only new chapters, make the output directory mandatory (no silent default), and harden image downloading so chapters are saved only when complete.

**Architecture:** A new pure `library.py` inspects the local download folder (parsing chapter numbers from `.cbz` filenames). `downloader.download_images` gains per-image retries and signals completeness via its return count. `komiku.py` resolves a mandatory output directory (flag or picker, error if neither), adds a `--update` flag, and only writes a chapter's `.cbz` when every page downloaded.

**Tech Stack:** Python 3, `requests`, `beautifulsoup4`, `pytest`. Existing modules: `client.py`, `parser.py`, `downloader.py`, `naming.py`, `ranges.py`, `models.py`, `komiku.py`.

---

## File Structure

- `library.py` — **new.** `existing_chapter_numbers(series_dir)` and `new_chapters(chapters, existing_numbers)`. Pure, no network.
- `downloader.py` — **modify.** Add per-image retries to `download_images`.
- `komiku.py` — **modify.** Mandatory output dir; `-u/--update` flag; completeness gate before writing `.cbz`; update-mode chapter selection.
- `tests/test_library.py` — **new.**
- `tests/test_downloader.py` — **modify.** Add retry tests.
- `tests/test_cli.py` — **modify.** Update picker tests to no-default contract; add update-mode and output-required tests.
- `README.md` — **modify.** Document `--update` and mandatory output dir.

---

### Task 1: `library.py` — existing chapter numbers

**Files:**
- Create: `library.py`
- Test: `tests/test_library.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_library.py
from library import existing_chapter_numbers


def test_existing_chapter_numbers_parses_integers_and_decimals(tmp_path):
    (tmp_path / "Naruto - Chapter 1.cbz").write_bytes(b"x")
    (tmp_path / "Naruto - Chapter 8.5.cbz").write_bytes(b"x")
    (tmp_path / "Naruto - Chapter 10.cbz").write_bytes(b"x")
    (tmp_path / "notes.txt").write_text("ignore me")
    assert existing_chapter_numbers(tmp_path) == {1.0, 8.5, 10.0}


def test_existing_chapter_numbers_missing_dir_is_empty(tmp_path):
    assert existing_chapter_numbers(tmp_path / "does-not-exist") == set()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_library.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'library'`

- [ ] **Step 3: Write minimal implementation**

```python
# library.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_library.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add library.py tests/test_library.py
git commit -m "feat: library.existing_chapter_numbers reads downloaded chapters"
```

---

### Task 2: `library.new_chapters` filter

**Files:**
- Modify: `library.py`
- Modify: `tests/test_library.py`

- [ ] **Step 1: Write the failing test (append to `tests/test_library.py`)**

```python
from library import new_chapters
from models import Chapter


def test_new_chapters_filters_present_preserving_order():
    chapters = [Chapter(n, f"u{n}") for n in (1.0, 2.0, 2.5, 3.0)]
    result = new_chapters(chapters, {1.0, 2.0})
    assert [c.number for c in result] == [2.5, 3.0]


def test_new_chapters_empty_when_all_present():
    chapters = [Chapter(n, f"u{n}") for n in (1.0, 2.0)]
    assert new_chapters(chapters, {1.0, 2.0}) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_library.py -v`
Expected: FAIL with ImportError for `new_chapters`

- [ ] **Step 3: Write minimal implementation (append to `library.py`)**

```python
def new_chapters(chapters, existing_numbers):
    """Chapters whose number is not already downloaded, order preserved."""
    return [c for c in chapters if c.number not in existing_numbers]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_library.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add library.py tests/test_library.py
git commit -m "feat: library.new_chapters filters out downloaded chapters"
```

---

### Task 3: Per-image retries in `download_images`

**Files:**
- Modify: `downloader.py`
- Modify: `tests/test_downloader.py`

**Current `downloader.py` `download_images`:**
```python
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

- [ ] **Step 1: Write the failing test (append to `tests/test_downloader.py`)**

```python
import downloader


class _Resp:
    def __init__(self, content):
        self.content = content


def test_download_images_retries_then_succeeds(monkeypatch):
    calls = {"n": 0}

    def fake_get(session, url, delay=0.0):
        calls["n"] += 1
        if calls["n"] < 3:
            raise TimeoutError("read timed out")
        return _Resp(b"ok")

    monkeypatch.setattr(downloader, "get", fake_get)
    images = downloader.download_images(None, ["u1"], delay=0, attempts=3)
    assert images == [b"ok"]
    assert calls["n"] == 3


def test_download_images_skips_after_exhausting_attempts(monkeypatch):
    calls = {"n": 0}

    def always_fail(session, url, delay=0.0):
        calls["n"] += 1
        raise TimeoutError("nope")

    monkeypatch.setattr(downloader, "get", always_fail)
    images = downloader.download_images(None, ["u1", "u2"], delay=0, attempts=3)
    assert images == []
    assert calls["n"] == 6  # 3 attempts per url, 2 urls


def test_download_images_returns_only_successes(monkeypatch):
    def half(session, url, delay=0.0):
        if url == "bad":
            raise TimeoutError("nope")
        return _Resp(b"good")

    monkeypatch.setattr(downloader, "get", half)
    images = downloader.download_images(None, ["good", "bad", "good"], delay=0, attempts=1)
    assert images == [b"good", b"good"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_downloader.py -v`
Expected: FAIL — `download_images` has no `attempts` parameter (TypeError) / retry behavior absent.

- [ ] **Step 3: Write minimal implementation (replace `download_images` in `downloader.py`)**

```python
def download_images(session, urls, delay=0.0, attempts=3):
    images = []
    for idx, url in enumerate(urls, start=1):
        for attempt in range(1, attempts + 1):
            try:
                resp = get(session, url, delay=delay)
                images.append(resp.content)
                break
            except Exception as exc:
                if attempt == attempts:
                    print(f"  ! skipped image {idx} ({url}) after {attempts} attempts: {exc}")
                else:
                    print(f"  . retry image {idx} ({url}): {exc}")
    return images
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_downloader.py -v`
Expected: PASS (all downloader tests, including the 3 new ones)

- [ ] **Step 5: Commit**

```bash
git add downloader.py tests/test_downloader.py
git commit -m "feat: retry images on transient failures before skipping"
```

---

### Task 4: Mandatory output directory (no default)

**Files:**
- Modify: `komiku.py`
- Modify: `tests/test_cli.py`

**Context:** `komiku.py` currently has:
```python
def select_output_dir(default):
    try:
        chosen = _ask_directory(default)
    except Exception as exc:
        print(f"(Folder picker unavailable: {exc}; using {default})")
        return Path(default)
    if not chosen:
        print(f"(No folder selected; using {default})")
        return Path(default)
    return Path(chosen)
```
and in `main()`:
```python
    if args.output:
        output_root = Path(args.output)
    else:
        output_root = select_output_dir(default_output_dir())
```
`default_output_dir()` returns `Path.home() / "Downloads" / "manga"`.

There are existing tests in `tests/test_cli.py` named
`test_select_output_dir_returns_chosen`, `test_select_output_dir_falls_back_on_cancel`,
and `test_select_output_dir_falls_back_when_picker_unavailable` that assert the
OLD default-fallback contract. They must be replaced.

- [ ] **Step 1: Replace the picker tests in `tests/test_cli.py`**

Delete these three existing tests:
```python
def test_select_output_dir_returns_chosen(monkeypatch):
    monkeypatch.setattr(komiku, "_ask_directory", lambda d: "D:/Manga")
    assert komiku.select_output_dir(Path.home() / "Downloads" / "manga") == Path("D:/Manga")


def test_select_output_dir_falls_back_on_cancel(monkeypatch):
    default = Path.home() / "Downloads" / "manga"
    monkeypatch.setattr(komiku, "_ask_directory", lambda d: "")
    assert komiku.select_output_dir(default) == default


def test_select_output_dir_falls_back_when_picker_unavailable(monkeypatch):
    default = Path.home() / "Downloads" / "manga"

    def boom(d):
        raise RuntimeError("no display")

    monkeypatch.setattr(komiku, "_ask_directory", boom)
    assert komiku.select_output_dir(default) == default
```

Replace them with the new no-default contract:
```python
def test_select_output_dir_returns_chosen(monkeypatch):
    monkeypatch.setattr(komiku, "_ask_directory", lambda d: "D:/Manga")
    assert komiku.select_output_dir() == Path("D:/Manga")


def test_select_output_dir_none_on_cancel(monkeypatch):
    monkeypatch.setattr(komiku, "_ask_directory", lambda d: "")
    assert komiku.select_output_dir() is None


def test_select_output_dir_none_when_picker_unavailable(monkeypatch):
    def boom(d):
        raise RuntimeError("no display")

    monkeypatch.setattr(komiku, "_ask_directory", boom)
    assert komiku.select_output_dir() is None


def test_main_errors_when_no_output_dir(monkeypatch, capsys):
    monkeypatch.setattr(komiku, "_ask_directory", lambda d: "")
    code = komiku.main(["naruto"])
    assert code == 2
    assert "output directory is required" in capsys.readouterr().out.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_cli.py -v`
Expected: FAIL — `select_output_dir()` still requires a `default` arg / still returns a default; `main` does not error.

- [ ] **Step 3: Update `select_output_dir` in `komiku.py`**

Replace the function with:
```python
def select_output_dir():
    """Open the folder picker and return the chosen Path, or None if the user
    cancelled or no GUI is available. There is no default fallback."""
    try:
        chosen = _ask_directory(default_output_dir())
    except Exception as exc:
        print(f"(Folder picker unavailable: {exc})")
        return None
    if not chosen:
        return None
    return Path(chosen)
```

(`default_output_dir()` is kept — it is now only the picker's suggested start
directory.)

- [ ] **Step 4: Update `main()` output resolution in `komiku.py`**

Replace:
```python
    if args.output:
        output_root = Path(args.output)
    else:
        output_root = select_output_dir(default_output_dir())
```
with:
```python
    if args.output:
        output_root = Path(args.output)
    else:
        output_root = select_output_dir()
        if output_root is None:
            print("Error: an output directory is required "
                  "(pass -o/--output or pick a folder).")
            return 2
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_cli.py -v`
Expected: PASS (including the 4 replaced/added tests)

- [ ] **Step 6: Commit**

```bash
git add komiku.py tests/test_cli.py
git commit -m "feat: require an output directory, drop silent default"
```

---

### Task 5: `--update` flag and update-mode selection

**Files:**
- Modify: `komiku.py`
- Modify: `tests/test_cli.py`

**Context:** Current `run()` signature and the relevant body in `komiku.py`:
```python
def run(title, chapters_spec, output_root, delay, force):
    ...
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
    ...
```
`main()` calls `run(args.title, args.chapters, output_root, args.delay, args.force)`.

This task adds update-mode selection. The `library` functions are imported.

- [ ] **Step 1: Write the failing test (append to `tests/test_cli.py`)**

```python
import library
from models import Chapter


def test_select_chapters_update_returns_only_new(monkeypatch, tmp_path):
    all_ch = [Chapter(n, f"u{n}") for n in (1.0, 2.0, 3.0)]
    monkeypatch.setattr(library, "existing_chapter_numbers", lambda d: {1.0, 2.0})
    selected, msg = komiku.select_chapters(all_ch, chapters_spec=None,
                                            update=True, series_dir=tmp_path)
    assert [c.number for c in selected] == [3.0]
    assert "1 new" in msg


def test_select_chapters_update_up_to_date(monkeypatch, tmp_path):
    all_ch = [Chapter(n, f"u{n}") for n in (1.0, 2.0)]
    monkeypatch.setattr(library, "existing_chapter_numbers", lambda d: {1.0, 2.0})
    selected, msg = komiku.select_chapters(all_ch, chapters_spec=None,
                                            update=True, series_dir=tmp_path)
    assert selected == []
    assert "up to date" in msg.lower()


def test_select_chapters_update_no_existing_downloads_all(monkeypatch, tmp_path):
    all_ch = [Chapter(n, f"u{n}") for n in (1.0, 2.0)]
    monkeypatch.setattr(library, "existing_chapter_numbers", lambda d: set())
    selected, msg = komiku.select_chapters(all_ch, chapters_spec=None,
                                            update=True, series_dir=tmp_path)
    assert [c.number for c in selected] == [1.0, 2.0]
    assert "no existing download" in msg.lower()


def test_select_chapters_range_mode_unchanged(tmp_path):
    all_ch = [Chapter(n, f"u{n}") for n in (1.0, 2.0, 3.0)]
    selected, msg = komiku.select_chapters(all_ch, chapters_spec="1-2",
                                            update=False, series_dir=tmp_path)
    assert [c.number for c in selected] == [1.0, 2.0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_cli.py -v`
Expected: FAIL — `komiku.select_chapters` does not exist.

- [ ] **Step 3: Add `select_chapters` and imports to `komiku.py`**

Add to the imports block:
```python
import library
```

Add this function (above `run`):
```python
def select_chapters(all_chapters, chapters_spec, update, series_dir):
    """Return (selected_chapters, message). In update mode, select chapters not
    already present in series_dir; otherwise apply the chapter range."""
    if update:
        existing = library.existing_chapter_numbers(series_dir)
        if not existing:
            return all_chapters, "No existing download found; fetching all chapters."
        new = library.new_chapters(all_chapters, existing)
        if not new:
            return [], f"Already up to date ({len(existing)} chapters)."
        labels = ", ".join(chapter_label(c.number) for c in new)
        return new, f"Found {len(new)} new chapter(s): {labels}"

    lo, hi = parse_range(chapters_spec)
    selected = filter_chapters(all_chapters, lo, hi)
    if lo is not None:
        present = {c.number for c in all_chapters}
        for n in _missing_integer_chapters(lo, hi, present):
            print(f"  ! chapter {chapter_label(n)} not available, skipping")
    return selected, ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_cli.py -v`
Expected: PASS (including the 4 new `select_chapters` tests)

- [ ] **Step 5: Commit**

```bash
git add komiku.py tests/test_cli.py
git commit -m "feat: select_chapters supports update mode"
```

---

### Task 6: Wire update mode + completeness gate into `run()` and `main()`

**Files:**
- Modify: `komiku.py`

**Context:** This task rewrites the body of `run()` to (a) use `select_chapters`, and (b) only write a `.cbz` when all images downloaded. The current download loop in `run()` is:
```python
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
```

- [ ] **Step 1: Update `run()` signature and selection block in `komiku.py`**

Change the signature:
```python
def run(title, chapters_spec, output_root, delay, force, update):
```

Replace the selection block (from `lo, hi = parse_range(...)` through the
`if not selected:` early return AND the `series_dir = ...` line) with:
```python
    series_dir = Path(output_root) / safe_filename(series_title)
    selected, message = select_chapters(all_chapters, chapters_spec, update, series_dir)
    if message:
        print(message)
    if not selected:
        if not update:
            print("No chapters matched the requested range.")
        return 0 if update else 1

    print(f"Downloading {len(selected)} chapter(s) of {series_title!r} to {series_dir}")
```

Note: `series_dir` must now be computed *before* `select_chapters` (it needs it).
Ensure there is no second `series_dir = ...` assignment left below.

- [ ] **Step 2: Replace the download loop body with the completeness gate**

```python
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
        if len(images) != len(image_urls):
            print(f"  ! Chapter {label} incomplete "
                  f"({len(images)}/{len(image_urls)} pages); "
                  f"not saving, will retry next run")
            continue
        build_cbz(images, out_path)
        print(f"    saved {out_path.name} ({len(images)} pages)")
```

- [ ] **Step 3: Update the `main()` call and add the `--update` flag**

Add the argument (next to the other `add_argument` calls):
```python
    parser.add_argument("-u", "--update", action="store_true",
                        help="download only chapters not already in the output "
                             "folder (ignores --chapters)")
```

Update the `run(...)` call:
```python
        return run(args.title, args.chapters, output_root, args.delay,
                   args.force, args.update)
```

- [ ] **Step 4: Run the full test suite**

Run: `.venv/Scripts/python -m pytest -v`
Expected: PASS (all tests across all files)

- [ ] **Step 5: Verify the CLI help shows `--update`**

Run: `.venv/Scripts/python komiku.py --help`
Expected: output includes `-u, --update` and the `-o/--output` help mentions the picker.

- [ ] **Step 6: Commit**

```bash
git add komiku.py
git commit -m "feat: wire update mode and skip incomplete chapters in run()"
```

---

### Task 7: Live verification + README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Live update-mode smoke test against the real download**

The earlier "Kichiku Eiyuu" run left chapters missing in
`~/Downloads/manga/Kichiku Eiyuu`. Run update mode against that folder
(use the actual folder; pass `-o` so no picker is needed):

Run:
```bash
.venv/Scripts/python komiku.py "kichiku eiyuu" --update -o "C:\Users\ediso\Downloads\manga"
```
Expected: prints `Found <N> new chapter(s): ...` listing the missing chapters
(0.1, 1–14, 8.5 and any previously-incomplete ones), then downloads them. After
it finishes, confirm the folder has more `.cbz` files than before and that a
re-run prints `Already up to date (...)`.

If anything fails to parse against the live site, capture the HTML and fix the
relevant parser + its fixture test before proceeding.

- [ ] **Step 2: Update `README.md` — add update mode and mandatory output**

In the Usage section, add an update example and adjust the output-dir wording.
Replace the existing "Choosing where to save" paragraph:
```markdown
**Choosing where to save:** if you don't pass `-o/--output`, a folder-picker
dialog opens so you can select the destination. Cancel it (or run on a machine
with no GUI) and it falls back to `~/Downloads/manga`. Pass `-o` to skip the
dialog entirely — useful for scripts.
```
with:
```markdown
**Choosing where to save (required):** you must always specify where manga is
saved. Either pass `-o/--output <folder>`, or omit it and pick a folder in the
dialog that opens. If you cancel the dialog (or run with no GUI and no `-o`), the
program prints an error and exits — there is no default location.

**Updating a series:** add `--update` (`-u`) to download only the chapters you
don't already have in the output folder:

\```powershell
.venv\Scripts\python komiku.py "kichiku eiyuu" --update -o "E:\Manga"
\```

It reports `Already up to date (...)` or `Found N new chapter(s): ...` and
fetches only the missing ones. `--update` ignores `--chapters`. Chapters whose
download is interrupted or incomplete are not saved as `.cbz`, so a later
`--update` (or re-run) re-fetches them cleanly.
```

(Remove the backslashes before the triple backticks — they are only here to
escape the fenced block inside this plan.)

Also update the flags table row for `--update`: add a row
`| \`-u\` / \`--update\` | Download only chapters missing from the output folder (ignores \`--chapters\`) |`
and change the `-o`/`--output` row to:
`| \`-o\` / \`--output\` | Output root folder. Required — pass it, or pick a folder in the dialog; no default |`

- [ ] **Step 3: Run the full suite once more**

Run: `.venv/Scripts/python -m pytest -q`
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: document update mode and required output directory"
```

---

## Self-Review Notes

- **Spec coverage:**
  - Required output dir (Change 1) → Task 4 (`select_output_dir` returns None, `main` errors with exit 2).
  - Update mode (Change 2) → Task 1+2 (`library`), Task 5 (`select_chapters`), Task 6 (wiring + `--update` flag), Task 7 (live verify).
  - Download robustness (Change 3) → Task 3 (per-image retries) + Task 6 Step 2 (completeness gate: write `.cbz` only when `len(images) == len(image_urls)`).
- **Supersedes:** Task 6 replaces the old "downloaded zero images" check with the completeness gate (zero is the `0 < total` case), matching the spec.
- **`--update` ignores `--chapters`:** `select_chapters` does not look at `chapters_spec` when `update=True`. ✅
- **Name consistency:** `existing_chapter_numbers`, `new_chapters`, `select_chapters(all_chapters, chapters_spec, update, series_dir)`, `select_output_dir()` (no args), `download_images(session, urls, delay, attempts)`, `run(title, chapters_spec, output_root, delay, force, update)` — used consistently across tasks.
- **series_dir ordering:** Task 6 explicitly moves `series_dir` computation above `select_chapters` and warns against a leftover duplicate assignment.
- **Update return code:** update mode returns 0 when up-to-date (not an error); range mode returns 1 when nothing matched — preserved in Task 6 Step 1.
