"""Profile compression: gzip-compress exported bundles to reduce storage size."""

from __future__ import annotations

import gzip
import json
import os
from pathlib import Path
from typing import Any


class CompressError(Exception):
    """Raised when compression or decompression fails."""


def compress_bundle(data: dict[str, Any], dest: Path) -> Path:
    """Serialize *data* as JSON and write a gzip-compressed file to *dest*.

    The file is always written with a ``.gz`` suffix.  If *dest* does not
    already end in ``.gz`` the suffix is appended automatically.

    Returns the final path that was written.
    """
    if not data:
        raise CompressError("Cannot compress an empty bundle.")

    out = dest if str(dest).endswith(".gz") else Path(str(dest) + ".gz")
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        payload = json.dumps(data, separators=(",", ":")).encode()
        with gzip.open(out, "wb") as fh:
            fh.write(payload)
    except (OSError, TypeError, ValueError) as exc:
        raise CompressError(f"Failed to compress bundle: {exc}") from exc

    return out


def decompress_bundle(src: Path) -> dict[str, Any]:
    """Read a gzip-compressed JSON bundle from *src* and return the decoded dict."""
    if not src.exists():
        raise CompressError(f"Compressed bundle not found: {src}")

    try:
        with gzip.open(src, "rb") as fh:
            raw = fh.read()
        return json.loads(raw.decode())
    except (OSError, gzip.BadGzipFile, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CompressError(f"Failed to decompress bundle: {exc}") from exc


def bundle_size(src: Path) -> int:
    """Return the compressed size in bytes of *src*, or -1 if the file is missing."""
    try:
        return os.path.getsize(src)
    except OSError:
        return -1
