"""The project page is built from this repository, never typed by hand.

Its figures about the current release come from the profile manifest at build
time. The two papers are frozen, so their values are constants in the build
script; they must agree with docs/PAPERS.md, the registry readers are sent to.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _builder():
    spec = importlib.util.spec_from_file_location("build_site", ROOT / "site" / "build_site.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_page_builds_with_every_placeholder_filled(tmp_path):
    builder = _builder()
    builder.build(ROOT, tmp_path)
    page = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert not re.search(r"\{\{[A-Z_0-9]+\}\}", page)
    assert (tmp_path / "assets" / "brand" / "topvenues-mark.svg").is_file()


def test_the_frozen_paper_values_match_the_registry():
    builder = _builder()
    registry = (ROOT / "docs" / "PAPERS.md").read_text(encoding="utf-8")
    for paper in (builder.PAPER_A, builder.PAPER_B):
        for key in ("sha", "release", "doi", "sol", "pages"):
            assert str(paper[key]) in registry, f"{key} of {paper['release']} is not in PAPERS.md"
        assert f"{paper['records']:,}" in registry
        assert paper["cmd"].splitlines()[-1] in registry
