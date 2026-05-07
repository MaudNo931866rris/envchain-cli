"""Tests for envchain.template."""

from __future__ import annotations

import pytest

from envchain.template import TemplateError, render_string, render_from_profile
from envchain.profile import Profile, save


# ---------------------------------------------------------------------------
# render_string
# ---------------------------------------------------------------------------

def test_render_dollar_brace_syntax():
    result = render_string("Hello, ${NAME}!", {"NAME": "World"})
    assert result == "Hello, World!"


def test_render_bare_dollar_syntax():
    result = render_string("Hello, $NAME!", {"NAME": "Alice"})
    assert result == "Hello, Alice!"


def test_render_mixed_syntax():
    result = render_string("$GREETING ${TARGET}", {"GREETING": "Hi", "TARGET": "Bob"})
    assert result == "Hi Bob"


def test_render_no_placeholders():
    result = render_string("no vars here", {})
    assert result == "no vars here"


def test_render_strict_raises_on_missing():
    with pytest.raises(TemplateError, match="MISSING"):
        render_string("value=${MISSING}", {}, strict=True)


def test_render_loose_leaves_unknown_unchanged():
    result = render_string("value=${MISSING}", {}, strict=False)
    assert result == "value=${MISSING}"


def test_render_multiple_missing_listed_in_error():
    with pytest.raises(TemplateError) as exc_info:
        render_string("$A $B $C", {"A": "1"}, strict=True)
    msg = str(exc_info.value)
    assert "B" in msg
    assert "C" in msg


def test_render_replaces_all_occurrences():
    result = render_string("${X}-${X}", {"X": "val"})
    assert result == "val-val"


# ---------------------------------------------------------------------------
# render_from_profile  (requires isolated store)
# ---------------------------------------------------------------------------

@pytest.fixture()
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_STORE_DIR", str(tmp_path))
    return tmp_path


def _seed(name: str, passphrase: str, variables: dict) -> None:
    p = Profile(name=name)
    for k, v in variables.items():
        p.set_var(k, v)
    save(p, passphrase)


def test_render_from_profile_substitutes_vars(isolated_store):
    _seed("myapp", "Secret1!", {"DB_HOST": "localhost", "DB_PORT": "5432"})
    result = render_from_profile(
        "host=${DB_HOST} port=$DB_PORT",
        "myapp",
        "Secret1!",
    )
    assert result == "host=localhost port=5432"


def test_render_from_profile_strict_raises_on_missing(isolated_store):
    _seed("myapp", "Secret1!", {"FOO": "bar"})
    with pytest.raises(TemplateError):
        render_from_profile("${FOO} ${UNDEFINED}", "myapp", "Secret1!", strict=True)


def test_render_from_profile_extra_overrides(isolated_store):
    _seed("myapp", "Secret1!", {"KEY": "profile_value"})
    result = render_from_profile(
        "${KEY}",
        "myapp",
        "Secret1!",
        extra={"KEY": "override"},
    )
    assert result == "override"
