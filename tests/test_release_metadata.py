import re
from pathlib import Path

import gapatlas

ROOT = Path(__file__).resolve().parents[1]


def test_versions_agree():
    py = re.search(r'^version\s*=\s*"([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M).group(1)
    cff = re.search(r"^version:\s*(\S+)", (ROOT / "CITATION.cff").read_text(encoding="utf-8"), re.M).group(1)
    assert py == gapatlas.__version__ == cff
    assert f"## {py}" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
