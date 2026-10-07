import pytest

from riftscout import updater
from riftscout.updater import UpdateError, parse_sha256sums, parse_version

H = "a" * 64


def test_parse_version():
    assert parse_version("v0.2.0") == (0, 2, 0)
    assert parse_version("1.3") == (1, 3, 0)
    assert parse_version("v1.10.2-beta") > parse_version("v1.9.9")
    assert parse_version("") == (0, 0, 0)


def test_parse_sha256sums():
    text = f"{H}  RiftScout.exe\n{'b' * 64} *Other.zip\nbad line\n"
    assert parse_sha256sums(text, "riftscout.exe") == H.upper()
    assert parse_sha256sums(text, "Other.zip") == ("b" * 64).upper()
    assert parse_sha256sums(text, "missing.exe") is None
    assert parse_sha256sums("nothex  RiftScout.exe", "RiftScout.exe") is None


def test_download_requires_checksum_file():
    with pytest.raises(UpdateError):
        updater.download_update({"asset_url": "https://github.com/x.exe", "sha_url": None})
    with pytest.raises(UpdateError):
        updater.download_update({"asset_url": None, "sha_url": "https://github.com/s"})


def test_download_rejects_hash_mismatch(tmp_path, monkeypatch):
    from riftscout import config as C, net
    monkeypatch.setattr(C, "UPDATES_DIR", tmp_path)
    monkeypatch.setattr(net, "fetch_bytes", lambda *a, **k: f"{H}  RiftScout.exe".encode())

    def fake_download(url, dest, progress_callback=None):
        open(dest, "wb").write(b"tampered")
        return True
    monkeypatch.setattr(net, "download_file", fake_download)
    with pytest.raises(UpdateError, match="checksum"):
        updater.download_update({"asset_url": "https://github.com/a", "sha_url": "https://github.com/b",
                                 "asset_name": "RiftScout.exe", "tag": "v9.9.9"})
    assert not list(tmp_path.glob("*.exe"))


def test_check_for_updates(monkeypatch):
    from riftscout import net
    release = {"tag_name": "v9.0.0", "assets": [
        {"name": "RiftScout.exe", "browser_download_url": "https://github.com/e"},
        {"name": "SHA256SUMS.txt", "browser_download_url": "https://github.com/s"}]}
    monkeypatch.setattr(net, "fetch_json", lambda *a, **k: release)
    info = updater.check_for_updates("0.2.0")
    assert info["asset_url"].endswith("/e") and info["sha_url"].endswith("/s")
    assert updater.check_for_updates("9.0.0") is None
