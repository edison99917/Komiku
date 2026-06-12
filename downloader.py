import zipfile
from pathlib import Path

from client import get


def build_cbz(images, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Pad to a width that keeps filenames lexicographically ordered even when a
    # chapter has 1000+ pages (readers sort by name: "1000" < "999" otherwise).
    width = max(3, len(str(len(images))))
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_STORED) as zf:
        for i, data in enumerate(images, start=1):
            zf.writestr(f"{i:0{width}d}.jpg", data)


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
