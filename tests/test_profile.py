"""Tests for the Profile model (envchain.profile)."""

import pytest

from envchain.profile import Profile

PASS = "s3cr3t"


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    yield


def test_set_and_get_var():
    p = Profile("proj")
    p.set_var("FOO", "bar")
    assert p.variables["FOO"] == "bar"


def test_unset_var():
    p = Profile("proj", {"A": "1", "B": "2"})
    p.unset_var("A")
    assert "A" not in p.variables
    assert "B" in p.variables


def test_unset_missing_var_raises():
    p = Profile("proj")
    with pytest.raises(KeyError, match="'MISSING'"):
        p.unset_var("MISSING")


def test_as_env_dict_is_copy():
    p = Profile("proj", {"X": "1"})
    env = p.as_env_dict()
    env["X"] = "mutated"
    assert p.variables["X"] == "1"


def test_save_and_load_roundtrip():
    p = Profile("myapp", {"TOKEN": "xyz", "ENV": "prod"})
    p.save(PASS)
    loaded = Profile.load("myapp", PASS)
    assert loaded.name == "myapp"
    assert loaded.variables == {"TOKEN": "xyz", "ENV": "prod"}


def test_list_all():
    for name in ("a", "b", "c"):
        Profile(name, {"K": "v"}).save(PASS)
    assert Profile.list_all() == ["a", "b", "c"]


def test_load_wrong_passphrase():
    Profile("secure", {"K": "v"}).save(PASS)
    with pytest.raises(Exception):
        Profile.load("secure", "badpass")


def test_load_nonexistent_profile():
    with pytest.raises(FileNotFoundError):
        Profile.load("ghost", PASS)
