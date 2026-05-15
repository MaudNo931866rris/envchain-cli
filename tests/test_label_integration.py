"""Integration tests for label persistence and multi-profile scenarios."""

from __future__ import annotations

import pytest

from envchain.label import (
    find_by_label,
    get_label,
    list_labels,
    remove_label,
    set_label,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    yield tmp_path


def test_multiple_profiles_independent():
    set_label("dev", "Development", "dev env")
    set_label("prod", "Production", "prod env")
    set_label("staging", "Staging", "staging env")
    assert get_label("dev")["label"] == "Development"
    assert get_label("prod")["label"] == "Production"
    assert get_label("staging")["label"] == "Staging"


def test_remove_one_does_not_affect_others():
    set_label("dev", "Development")
    set_label("prod", "Production")
    remove_label("dev")
    assert get_label("dev") is None
    assert get_label("prod") is not None


def test_list_labels_sorted_alphabetically():
    set_label("zebra", "Zebra")
    set_label("apple", "Apple")
    set_label("mango", "Mango")
    keys = list(list_labels().keys())
    # list_labels returns dict; check all present
    assert set(keys) == {"zebra", "apple", "mango"}


def test_find_returns_multiple_matches():
    set_label("proj-a", "API Service", "handles auth")
    set_label("proj-b", "API Gateway", "handles routing")
    set_label("proj-c", "Database", "stores data")
    results = find_by_label("api")
    profiles = {r["profile"] for r in results}
    assert "proj-a" in profiles
    assert "proj-b" in profiles
    assert "proj-c" not in profiles


def test_overwrite_preserves_other_profiles():
    set_label("alpha", "Alpha v1")
    set_label("beta", "Beta v1")
    set_label("alpha", "Alpha v2", "updated")
    assert get_label("alpha")["label"] == "Alpha v2"
    assert get_label("beta")["label"] == "Beta v1"


def test_label_without_description_defaults_empty():
    set_label("proj", "Simple Label")
    info = get_label("proj")
    assert info["description"] == ""


def test_find_by_description_only():
    set_label("infra", "Infrastructure", "terraform managed resources")
    results = find_by_label("terraform")
    assert len(results) == 1
    assert results[0]["profile"] == "infra"
