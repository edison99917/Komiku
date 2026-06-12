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
