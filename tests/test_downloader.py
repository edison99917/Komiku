import zipfile
from pathlib import Path

import downloader
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


def test_build_cbz_lexicographic_order_past_999_pages(tmp_path):
    images = [b"x"] * 1000
    out = tmp_path / "big.cbz"
    build_cbz(images, out)
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
        # 4-digit padding so lexical sort matches numeric (insertion) order
        assert names[0] == "0001.jpg"
        assert names[-1] == "1000.jpg"
        assert sorted(names) == names


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
