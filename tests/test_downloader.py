import zipfile
from pathlib import Path

from downloader import build_cbz


def test_build_cbz_writes_padded_ordered_images(tmp_path):
    images = [b"img-a", b"img-b", b"img-c"]
    out = tmp_path / "Naruto - Chapter 1.cbz"
    build_cbz(images, out)
    assert out.exists()
    with zipfile.ZipFile(out) as zf:
        names = sorted(zf.namelist())
        assert names == ["001.jpg", "002.jpg", "003.jpg"]
        assert zf.read("001.jpg") == b"img-a"
        assert zf.read("003.jpg") == b"img-c"


def test_build_cbz_creates_parent_dirs(tmp_path):
    out = tmp_path / "Naruto" / "Naruto - Chapter 1.cbz"
    build_cbz([b"x"], out)
    assert out.exists()
