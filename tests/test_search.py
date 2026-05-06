"""Tests for envchain.search."""

from __future__ import annotations

import pytest

from envchain.profile import Profile, save
from envchain.search import SearchResult, search_profiles


@pytest.fixture()
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr("envchain.store._store_dir", lambda: tmp_path)
    monkeypatch.setattr("envchain.profile._store_dir", lambda: tmp_path, raising=False)
    return tmp_path


PASS = "hunter2"


def _seed(name: str, tmp_path, vars: dict) -> None:
    p = Profile(name)
    for k, v in vars.items():
        p.set_var(k, v)
    save(p, PASS)


def test_search_finds_key_match(isolated_store):
    _seed("myproject", isolated_store, {"DATABASE_URL": "postgres://", "SECRET_KEY": "abc"})
    results = search_profiles(["myproject"], PASS, "DATABASE")
    assert len(results) == 1
    assert results[0].key == "DATABASE_URL"
    assert results[0].profile_name == "myproject"


def test_search_case_insensitive_by_default(isolated_store):
    _seed("proj", isolated_store, {"API_TOKEN": "tok"})
    results = search_profiles(["proj"], PASS, "api_token")
    assert len(results) == 1


def test_search_case_sensitive_no_match(isolated_store):
    _seed("proj", isolated_store, {"API_TOKEN": "tok"})
    results = search_profiles(["proj"], PASS, "api_token", case_sensitive=True)
    assert results == []


def test_search_values(isolated_store):
    _seed("proj", isolated_store, {"FOO": "special_value", "BAR": "other"})
    results = search_profiles(["proj"], PASS, "special", search_values=True)
    assert len(results) == 1
    assert results[0].key == "FOO"


def test_search_no_value_preview_by_default(isolated_store):
    _seed("proj", isolated_store, {"KEY": "secret"})
    results = search_profiles(["proj"], PASS, "KEY")
    assert results[0].value_preview is None


def test_search_show_values_truncates_long_value(isolated_store):
    long_val = "x" * 80
    _seed("proj", isolated_store, {"LONG_KEY": long_val})
    results = search_profiles(["proj"], PASS, "LONG_KEY", show_values=True)
    preview = results[0].value_preview
    assert preview is not None
    assert preview.endswith("...")
    assert len(preview) <= 43


def test_search_multiple_profiles(isolated_store):
    _seed("alpha", isolated_store, {"SHARED": "1", "ALPHA_ONLY": "2"})
    _seed("beta", isolated_store, {"SHARED": "3", "BETA_ONLY": "4"})
    results = search_profiles(["alpha", "beta"], PASS, "SHARED")
    assert len(results) == 2
    names = {r.profile_name for r in results}
    assert names == {"alpha", "beta"}


def test_search_skips_bad_passphrase_profile(isolated_store):
    _seed("good", isolated_store, {"KEY": "val"})
    _seed("bad", isolated_store, {"KEY": "val"})
    # Only pass wrong passphrase implicitly by using a profile saved with different pass
    from envchain.profile import Profile, save as psave
    p2 = Profile("bad")
    p2.set_var("KEY", "val")
    psave(p2, "different_pass")
    results = search_profiles(["good", "bad"], PASS, "KEY")
    # Should still return result from 'good', skip 'bad'
    assert any(r.profile_name == "good" for r in results)


def test_result_as_dict(isolated_store):
    _seed("proj", isolated_store, {"MY_KEY": "val"})
    results = search_profiles(["proj"], PASS, "MY_KEY", show_values=True)
    d = results[0].as_dict()
    assert d["profile"] == "proj"
    assert d["key"] == "MY_KEY"
    assert "value_preview" in d
