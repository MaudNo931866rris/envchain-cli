"""Tests for envchain.lint."""

from __future__ import annotations

import os
import pytest

from envchain.profile import Profile, save
from envchain import store
from envchain.lint import lint_profile, LintError, LintIssue


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "_store_dir", lambda: tmp_path / "store")
    (tmp_path / "store").mkdir()
    yield tmp_path


def _seed(name: str, passphrase: str, vars: dict) -> None:
    p = Profile(name=name)
    for k, v in vars.items():
        p.set_var(k, v)
    save(p, passphrase)


def test_clean_profile_has_no_issues(isolated_store):
    _seed("myapp", "Secret1!", {"DATABASE_URL": "postgres://localhost/db", "API_KEY": "abc123"})
    result = lint_profile("myapp", "Secret1!")
    assert result.clean
    assert result.ok


def test_lowercase_key_produces_warning(isolated_store):
    _seed("myapp", "Secret1!", {"database_url": "postgres://localhost"})
    result = lint_profile("myapp", "Secret1!")
    keys = [i.key for i in result.issues]
    assert "database_url" in keys
    issue = next(i for i in result.issues if i.key == "database_url")
    assert issue.severity == "warning"
    assert "lowercase" in issue.message


def test_empty_value_produces_warning(isolated_store):
    _seed("myapp", "Secret1!", {"EMPTY_VAR": ""})
    result = lint_profile("myapp", "Secret1!")
    issue = next((i for i in result.issues if i.key == "EMPTY_VAR"), None)
    assert issue is not None
    assert issue.severity == "warning"
    assert "empty" in issue.message.lower()


def test_value_with_whitespace_produces_warning(isolated_store):
    _seed("myapp", "Secret1!", {"PADDED": "  value  "})
    result = lint_profile("myapp", "Secret1!")
    issue = next((i for i in result.issues if i.key == "PADDED"), None)
    assert issue is not None
    assert issue.severity == "warning"
    assert "whitespace" in issue.message.lower()


def test_underscore_prefix_key_produces_warning(isolated_store):
    _seed("myapp", "Secret1!", {"_INTERNAL": "val"})
    result = lint_profile("myapp", "Secret1!")
    issue = next((i for i in result.issues if i.key == "_INTERNAL"), None)
    assert issue is not None
    assert issue.severity == "warning"


def test_ok_is_false_when_error_present(isolated_store):
    _seed("myapp", "Secret1!", {"BAD KEY!": "val"})
    result = lint_profile("myapp", "Secret1!")
    assert not result.ok


def test_wrong_passphrase_raises_lint_error(isolated_store):
    _seed("myapp", "Secret1!", {"FOO": "bar"})
    with pytest.raises(LintError):
        lint_profile("myapp", "wrongpass")


def test_as_dict_on_issue():
    issue = LintIssue(key="FOO", severity="warning", message="some message")
    d = issue.as_dict()
    assert d == {"key": "FOO", "severity": "warning", "message": "some message"}


def test_multiple_issues_accumulate(isolated_store):
    _seed("myapp", "Secret1!", {"lower_key": ""})
    result = lint_profile("myapp", "Secret1!")
    keys = [i.key for i in result.issues]
    # Both a key warning and an empty-value warning for the same key
    assert keys.count("lower_key") >= 2
