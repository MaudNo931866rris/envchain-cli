"""Tests for envchain.passphrase — strength validation and policy enforcement."""

import pytest

from envchain.passphrase import (
    PassphraseError,
    PassphrasePolicy,
    PassphraseStrength,
    check_passphrase,
    enforce_passphrase,
)


# ---------------------------------------------------------------------------
# check_passphrase — default policy
# ---------------------------------------------------------------------------


def test_strong_passphrase_passes_default_policy():
    result = check_passphrase("CorrectHorse42!")
    assert result.ok is True
    assert result.violations == []


def test_too_short_fails():
    result = check_passphrase("Short1A")
    assert result.ok is False
    assert any("at least 12" in v for v in result.violations)


def test_missing_uppercase_fails():
    result = check_passphrase("alllowercase42")
    assert result.ok is False
    assert any("uppercase" in v for v in result.violations)


def test_missing_lowercase_fails():
    result = check_passphrase("ALLUPPERCASE42")
    assert result.ok is False
    assert any("lowercase" in v for v in result.violations)


def test_missing_digit_fails():
    result = check_passphrase("NoDigitsHereABC")
    assert result.ok is False
    assert any("digit" in v for v in result.violations)


def test_multiple_violations_reported():
    result = check_passphrase("short")
    assert len(result.violations) >= 2


# ---------------------------------------------------------------------------
# check_passphrase — custom policy
# ---------------------------------------------------------------------------


def test_custom_policy_require_special():
    policy = PassphrasePolicy(min_length=8, require_special=True)
    result = check_passphrase("NoSpecial1A", policy)
    assert result.ok is False
    assert any("special" in v for v in result.violations)


def test_custom_policy_relaxed_length():
    policy = PassphrasePolicy(min_length=4, require_uppercase=False, require_digit=False)
    result = check_passphrase("abcd", policy)
    assert result.ok is True


# ---------------------------------------------------------------------------
# score heuristic
# ---------------------------------------------------------------------------


def test_score_range():
    for pw in ["a", "aaaaaaaa", "Abcdefgh1", "CorrectHorse42!"]:
        r = check_passphrase(pw)
        assert 0 <= r.score <= 4


def test_long_mixed_passphrase_scores_high():
    result = check_passphrase("CorrectHorse42!")
    assert result.score >= 3


def test_very_short_scores_low():
    result = check_passphrase("ab")
    assert result.score <= 1


# ---------------------------------------------------------------------------
# enforce_passphrase
# ---------------------------------------------------------------------------


def test_enforce_raises_on_weak_passphrase():
    with pytest.raises(PassphraseError, match="does not meet requirements"):
        enforce_passphrase("weak")


def test_enforce_does_not_raise_on_strong_passphrase():
    enforce_passphrase("CorrectHorse42")  # should not raise


# ---------------------------------------------------------------------------
# __str__ representation
# ---------------------------------------------------------------------------


def test_str_includes_label():
    result = PassphraseStrength(ok=True, score=3)
    assert "strong" in str(result)


def test_str_includes_violations_when_present():
    result = PassphraseStrength(ok=False, score=1, violations=["too short"])
    assert "too short" in str(result)
