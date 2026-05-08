"""Profile linting: detect common issues with variable names and values."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from envchain.profile import load


class LintError(Exception):
    """Raised when linting cannot be performed (e.g. bad passphrase)."""


@dataclass
class LintIssue:
    key: str
    severity: str          # 'warning' | 'error'
    message: str

    def as_dict(self) -> dict:
        return {"key": self.key, "severity": self.severity, "message": self.message}


@dataclass
class LintResult:
    profile: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def clean(self) -> bool:
        return len(self.issues) == 0


_VALID_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')
_LOWER_KEY_RE = re.compile(r'[a-z]')


def _check_key(key: str) -> List[LintIssue]:
    issues: List[LintIssue] = []
    if not key:
        issues.append(LintIssue(key=key, severity="error", message="Variable name is empty"))
        return issues
    if not _VALID_KEY_RE.match(key):
        if _LOWER_KEY_RE.search(key):
            issues.append(LintIssue(key=key, severity="warning",
                                     message="Variable name contains lowercase letters; consider uppercasing"))
        else:
            issues.append(LintIssue(key=key, severity="error",
                                     message="Variable name contains invalid characters"))
    if key.startswith('_'):
        issues.append(LintIssue(key=key, severity="warning",
                                 message="Variable name starts with underscore"))
    return issues


def _check_value(key: str, value: str) -> List[LintIssue]:
    issues: List[LintIssue] = []
    if value == "":
        issues.append(LintIssue(key=key, severity="warning", message="Value is empty string"))
    if value != value.strip():
        issues.append(LintIssue(key=key, severity="warning",
                                 message="Value has leading or trailing whitespace"))
    return issues


def lint_profile(profile_name: str, passphrase: str) -> LintResult:
    """Load *profile_name* and return a LintResult describing any issues found."""
    try:
        prof = load(profile_name, passphrase)
    except Exception as exc:
        raise LintError(str(exc)) from exc

    result = LintResult(profile=profile_name)
    env = prof.as_env_dict()
    for key, value in env.items():
        result.issues.extend(_check_key(key))
        result.issues.extend(_check_value(key, value))
    return result
