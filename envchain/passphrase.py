"""Passphrase strength validation and policy enforcement for envchain profiles."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List


class PassphraseError(ValueError):
    """Raised when a passphrase does not meet policy requirements."""


@dataclass
class PassphrasePolicy:
    min_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = False
    special_chars: str = r"""!@#$%^&*()-_=+[]{}|;:',.<>?/`~\"""


@dataclass
class PassphraseStrength:
    ok: bool
    score: int  # 0-4
    violations: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        labels = ["very weak", "weak", "fair", "strong", "very strong"]
        label = labels[max(0, min(self.score, 4))]
        if self.violations:
            return f"{label} (issues: {'; '.join(self.violations)})"
        return label


def check_passphrase(
    passphrase: str,
    policy: PassphrasePolicy | None = None,
) -> PassphraseStrength:
    """Evaluate *passphrase* against *policy* and return a strength report."""
    if policy is None:
        policy = PassphrasePolicy()

    violations: List[str] = []

    if len(passphrase) < policy.min_length:
        violations.append(
            f"must be at least {policy.min_length} characters (got {len(passphrase)})"
        )
    if policy.require_uppercase and not re.search(r"[A-Z]", passphrase):
        violations.append("must contain at least one uppercase letter")
    if policy.require_lowercase and not re.search(r"[a-z]", passphrase):
        violations.append("must contain at least one lowercase letter")
    if policy.require_digit and not re.search(r"\d", passphrase):
        violations.append("must contain at least one digit")
    if policy.require_special and not any(
        ch in policy.special_chars for ch in passphrase
    ):
        violations.append("must contain at least one special character")

    # Simple scoring heuristic (independent of policy)
    score = 0
    if len(passphrase) >= 8:
        score += 1
    if len(passphrase) >= 16:
        score += 1
    if re.search(r"[A-Z]", passphrase) and re.search(r"[a-z]", passphrase):
        score += 1
    if re.search(r"\d", passphrase):
        score += 1
    if any(ch in policy.special_chars for ch in passphrase):
        score = min(score + 1, 4)

    return PassphraseStrength(ok=len(violations) == 0, score=score, violations=violations)


def enforce_passphrase(passphrase: str, policy: PassphrasePolicy | None = None) -> None:
    """Like :func:`check_passphrase` but raises :exc:`PassphraseError` on failure."""
    result = check_passphrase(passphrase, policy)
    if not result.ok:
        raise PassphraseError(
            "Passphrase does not meet requirements: " + "; ".join(result.violations)
        )
