"""Render shell-style templates using variables from an envchain profile."""

from __future__ import annotations

import re
from typing import Dict, Optional

from envchain.profile import load

_VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


class TemplateError(Exception):
    """Raised when template rendering fails."""


def render_string(template: str, variables: Dict[str, str], strict: bool = True) -> str:
    """Replace ``$VAR`` / ``${VAR}`` placeholders with *variables*.

    Parameters
    ----------
    template:
        Raw template text.
    variables:
        Mapping of variable name -> value.
    strict:
        When *True* (default) raise :class:`TemplateError` for any placeholder
        whose name is not present in *variables*.  When *False* leave the
        placeholder unchanged.
    """
    missing: list[str] = []

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        name = match.group(1) or match.group(2)
        if name in variables:
            return variables[name]
        if strict:
            missing.append(name)
            return match.group(0)
        return match.group(0)

    result = _VAR_RE.sub(_replace, template)
    if missing:
        raise TemplateError(
            f"Template references undefined variable(s): {', '.join(sorted(missing))}"
        )
    return result


def render_from_profile(
    template: str,
    profile_name: str,
    passphrase: str,
    strict: bool = True,
    extra: Optional[Dict[str, str]] = None,
) -> str:
    """Load *profile_name* and render *template* with its variables.

    *extra* values (if provided) are merged on top of the profile variables
    and take precedence.
    """
    profile = load(profile_name, passphrase)
    variables: Dict[str, str] = {**profile.as_env_dict(), **(extra or {})}
    return render_string(template, variables, strict=strict)
