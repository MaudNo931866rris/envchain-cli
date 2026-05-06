"""Tests for envchain.export — profile export/import feature."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from envchain.export import ExportError, export_profile, import_profile
from envchain.store import _store_dir, load_profile, save_profile

PASSPHRASE = "test-secret"
PROFILE = "myproject"
VARS = {"API_KEY": "abc123", "DEBUG": "true"}


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_STORE_DIR", str(tmp_path))
    yield tmp_path


def _seed_profile():
    save_profile(PROFILE, VARS, PASSPHRASE)


def test_export_creates_bundle_file(isolated_store):
    _seed_profile()
    out = isolated_store / "myproject.envbundle"
    export_profile(PROFILE, PASSPHRASE, out)
    assert out.exists()


def test_bundle_is_valid_json(isolated_store):
    _seed_profile()
    out = isolated_store / "myproject.envbundle"
    export_profile(PROFILE, PASSPHRASE, out)
    bundle = json.loads(out.read_text())
    assert bundle["version"] == 1
    assert bundle["profile"] == PROFILE
    assert "data" in bundle


def test_roundtrip_preserves_vars(isolated_store):
    _seed_profile()
    bundle_path = isolated_store / "export.envbundle"
    export_profile(PROFILE, PASSPHRASE, bundle_path)

    # Remove original so we can cleanly import
    from envchain.store import delete_profile
    delete_profile(PROFILE)

    imported_name = import_profile(bundle_path, PASSPHRASE)
    assert imported_name == PROFILE
    result = load_profile(PROFILE, PASSPHRASE)
    assert result == VARS


def test_import_with_rename(isolated_store):
    _seed_profile()
    bundle_path = isolated_store / "export.envbundle"
    export_profile(PROFILE, PASSPHRASE, bundle_path)

    imported_name = import_profile(bundle_path, PASSPHRASE, rename="renamed")
    assert imported_name == "renamed"
    result = load_profile("renamed", PASSPHRASE)
    assert result == VARS


def test_import_raises_if_profile_exists(isolated_store):
    _seed_profile()
    bundle_path = isolated_store / "export.envbundle"
    export_profile(PROFILE, PASSPHRASE, bundle_path)

    with pytest.raises(ExportError, match="already exists"):
        import_profile(bundle_path, PASSPHRASE)


def test_import_overwrite_succeeds(isolated_store):
    _seed_profile()
    bundle_path = isolated_store / "export.envbundle"
    export_profile(PROFILE, PASSPHRASE, bundle_path)

    imported_name = import_profile(bundle_path, PASSPHRASE, overwrite=True)
    assert imported_name == PROFILE


def test_import_wrong_passphrase_raises(isolated_store):
    _seed_profile()
    bundle_path = isolated_store / "export.envbundle"
    export_profile(PROFILE, PASSPHRASE, bundle_path)

    from envchain.store import delete_profile
    delete_profile(PROFILE)

    with pytest.raises(Exception):
        import_profile(bundle_path, "wrong-passphrase")


def test_import_missing_bundle_raises(isolated_store):
    with pytest.raises(ExportError, match="Cannot read bundle"):
        import_profile(isolated_store / "nonexistent.envbundle", PASSPHRASE)


def test_import_bad_version_raises(isolated_store):
    bad_bundle = isolated_store / "bad.envbundle"
    bad_bundle.write_text(json.dumps({"version": 99, "profile": "x", "data": ""}))
    with pytest.raises(ExportError, match="Unsupported bundle version"):
        import_profile(bad_bundle, PASSPHRASE)
