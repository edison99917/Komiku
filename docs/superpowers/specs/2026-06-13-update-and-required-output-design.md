# Update Mode + Required Output Directory — Design

**Date:** 2026-06-13
**Status:** Approved (pending spec review)

## Purpose

Two related changes to the Komiku Downloader:

1. **Required output directory.** The program must never save to a silent
   default. The user always specifies where manga goes — via `-o/--output` or
   by choosing a folder in the picker. If neither is provided, the program errors
   and exits.
2. **Update mode (`--update`).** Given a title and an output location, check the
   site for chapters not already downloaded and fetch only the new ones.

## Decisions

| Decision | Choice |
|----------|--------|
| Output directory | Mandatory — no default fallback |
| How it's provided | `-o/--output` flag, or the folder picker when `-o` is omitted |
| Picker cancelled / no GUI / nothing given | Print an error and exit non-zero (code 2); do **not** default |
| Update scope | A single title the user types |
| New chapters found | Download automatically (no confirm prompt) |
| Existing-chapter detection | Parse chapter numbers from `.cbz` filenames in the series folder (no state file) |
| `--update` vs `--chapters` | `--update` ignores `--chapters` (update = "everything new") |

## Change 1: Required output directory

This adjusts the previously-shipped folder-picker behavior (which fell back to
`~/Downloads/manga`). The fallback is removed.

**Resolution order in `main()`:**
1. `args.output` given → `output_root = Path(args.output)`.
2. Otherwise → `output_root = select_output_dir()` (opens the picker).
   - If it returns `None` (user cancelled, or no GUI available) →
     print `Error: an output directory is required (pass -o/--output or pick a folder).`
     and return exit code `2`.

**`select_output_dir()`** changes: it no longer takes/returns a default. It opens
the picker (using `~/Downloads/manga` only as the dialog's *suggested* start
directory) and returns the chosen `Path`, or `None` on cancel / unavailable GUI.

`default_output_dir()` is retained solely as the picker's suggested start
directory — it is never used as a silent destination.

## Change 2: Update mode

**Usage**
```
komiku.py "kichiku eiyuu" --update -o "E:\Manga"
komiku.py "kichiku eiyuu" -u            # omit -o -> pick the library folder
```

**Flow when `--update` is set** (inside `run()`):
1. Search → `choose_result` → fetch series page (unchanged) to get the real
   series title and the full site chapter list.
2. Compute the series folder: `<output_root>/<safe_filename(series_title)>/`.
3. `existing = library.existing_chapter_numbers(series_dir)` — read `.cbz`
   filenames in that folder and parse their chapter numbers.
4. `new = library.new_chapters(all_chapters, existing)`.
5. Report and act:
   - `existing` empty (folder absent/empty) →
     `"No existing download found; fetching all chapters."` then download all.
   - `new` empty → `"Already up to date (<N> chapters)."` and return 0.
   - otherwise → `"Found <K> new chapter(s): <labels>"` then download `new`.
6. The normal "skip if `.cbz` already exists" guard in the download loop stays as
   a safety net.

When `--update` is **not** set, behavior is unchanged (range filtering, etc.).

## New module: `library.py`

One responsibility: inspect the local library. No network.

```python
existing_chapter_numbers(series_dir) -> set[float]
    # Parse "<...> - Chapter <N>.cbz" filenames in series_dir.
    # Matches integers and decimals (e.g. 8.5) case-insensitively.
    # Returns an empty set if series_dir does not exist.

new_chapters(chapters, existing_numbers) -> list[Chapter]
    # Pure filter: chapters whose .number is not in existing_numbers,
    # preserving input order.
```

Filename pattern: `Chapter\s+([0-9]+(?:\.[0-9]+)?)\.cbz$`, case-insensitive.

## `komiku.py` changes

- Add `-u/--update` flag (`action="store_true"`).
- `run(...)` gains an `update` parameter; when true it computes `new` via
  `library` and uses it as the download list (with the report), bypassing range
  filtering.
- `main()` resolves the output directory per Change 1 and passes `args.update`
  through.

## Error handling

- No output directory → error + exit 2 (Change 1).
- Update against a never-downloaded title → treated as "download everything"
  with an informative message (not an error).
- All existing network/empty-chapter handling is unchanged.

## Testing

- `library.existing_chapter_numbers`: a tmp folder containing
  `X - Chapter 1.cbz`, `X - Chapter 8.5.cbz`, a non-`.cbz` file, and a missing
  folder → correct set / empty set.
- `library.new_chapters`: filters by number, preserves order, empty when all
  present.
- CLI: `select_output_dir()` returns `None` on cancel and on picker failure
  (via the `_ask_directory` seam); `main()` exits non-zero when no directory is
  resolved. (Existing picker tests are updated to the new no-default contract.)

## Out of scope (YAGNI)

- Scanning/updating the whole library at once (single title only, for now).
- A persisted index/state file (filenames are the source of truth).
- Confirmation prompts before downloading new chapters.
