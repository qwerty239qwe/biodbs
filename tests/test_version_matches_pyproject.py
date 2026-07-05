"""Guard: biodbs.__version__ must match pyproject.toml [project].version.

This catches the (easy to make) mistake of bumping one but not the other.
"""

import re
from pathlib import Path

import biodbs


def _pyproject_version() -> str:
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    # The project version is the only top-level `version = "..."` line
    # (dependency-group entries live inside list literals, not at column 0).
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        match = re.match(r'version\s*=\s*"([^"]+)"', line)
        if match:
            return match.group(1)
    raise AssertionError("no top-level version found in pyproject.toml")


def test_version_matches_pyproject():
    declared = _pyproject_version()
    assert biodbs.__version__ == declared, (
        f"biodbs.__version__={biodbs.__version__!r} != pyproject {declared!r}"
    )
