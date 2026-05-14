"""Tests for envchain.compress."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from envchain.compress import CompressError, bundle_size, compress_bundle, decompress_bundle


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_SAMPLE: dict = {
    "profile": "myapp",
    "vars": {"API_KEY": "abc123", "DEBUG": "true"},
}


# ---------------------------------------------------------------------------
# compress_bundle
# ---------------------------------------------------------------------------

def test_compress_creates_gz_file(tmp_path: Path) -> None:
    out = compress_bundle(_SAMPLE, tmp_path / "bundle.json")
    assert out.exists()
    assert str(out).endswith(".gz")


def test_compress_appends_gz_suffix_when_missing(tmp_path: Path) -> None:
    out = compress_bundle(_SAMPLE, tmp_path / "bundle")
    assert out.name == "bundle.gz"


def test_compress_does_not_double_suffix(tmp_path: Path) -> None:
    out = compress_bundle(_SAMPLE, tmp_path / "bundle.gz")
    assert out.name == "bundle.gz"


def test_compress_produces_valid_gzip(tmp_path: Path) -> None:
    out = compress_bundle(_SAMPLE, tmp_path / "bundle.gz")
    with gzip.open(out, "rb") as fh:
        raw = fh.read()
    assert json.loads(raw) == _SAMPLE


def test_compress_empty_dict_raises(tmp_path: Path) -> None:
    with pytest.raises(CompressError, match="empty"):
        compress_bundle({}, tmp_path / "bundle.gz")


# ---------------------------------------------------------------------------
# decompress_bundle
# ---------------------------------------------------------------------------

def test_decompress_roundtrip(tmp_path: Path) -> None:
    out = compress_bundle(_SAMPLE, tmp_path / "bundle.gz")
    result = decompress_bundle(out)
    assert result == _SAMPLE


def test_decompress_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(CompressError, match="not found"):
        decompress_bundle(tmp_path / "ghost.gz")


def test_decompress_corrupt_file_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.gz"
    bad.write_bytes(b"not gzip data at all")
    with pytest.raises(CompressError, match="Failed to decompress"):
        decompress_bundle(bad)


def test_decompress_valid_gzip_invalid_json_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad_json.gz"
    with gzip.open(bad, "wb") as fh:
        fh.write(b"{not valid json")
    with pytest.raises(CompressError, match="Failed to decompress"):
        decompress_bundle(bad)


# ---------------------------------------------------------------------------
# bundle_size
# ---------------------------------------------------------------------------

def test_bundle_size_returns_positive_int(tmp_path: Path) -> None:
    out = compress_bundle(_SAMPLE, tmp_path / "bundle.gz")
    assert bundle_size(out) > 0


def test_bundle_size_missing_file_returns_minus_one(tmp_path: Path) -> None:
    assert bundle_size(tmp_path / "ghost.gz") == -1
