"""
Unit tests for updater version comparison and SHA calculation.
"""

from pathlib import Path
from riftscout.updater import parse_version, calculate_sha256


def test_parse_version():
    assert parse_version("v0.1.0") == (0, 1, 0)
    assert parse_version("1.2.3") == (1, 2, 3)
    assert parse_version("v1.4.0-rc1") == (1, 4, 0)
    assert parse_version("invalid") == (0, 0, 0)

    # Comparison tests
    assert parse_version("v0.2.0") > parse_version("v0.1.0")
    assert parse_version("v1.0.0") > parse_version("v0.9.9")
    assert parse_version("v0.1.0") == parse_version("0.1.0")


def test_calculate_sha256(tmp_path: Path):
    test_file = tmp_path / "test.bin"
    test_file.write_bytes(b"RiftScout-Test-Payload")
    sha = calculate_sha256(test_file)
    assert len(sha) == 64
    assert sha == sha.upper()
