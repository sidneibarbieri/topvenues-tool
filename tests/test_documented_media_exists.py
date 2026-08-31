"""Every media file the documentation points at must be in the repository.

Replacing a recording leaves the old filename behind in a README, a demo page
and a caption track. A reader then follows a link to nothing, which no test of
the application itself would ever notice.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = [ROOT / "README.md", *(ROOT / "docs").rglob("*.md"), *(ROOT / "docs").rglob("*.html")]
MEDIA = re.compile(r"(?:\(|src=\"|poster=\")([^\s\"')]+\.(?:mp4|jpg|png|srt|vtt|json))")


def _referenced() -> list[tuple[Path, str]]:
    found = []
    for document in DOCUMENTS:
        for match in MEDIA.finditer(document.read_text(encoding="utf-8")):
            reference = match.group(1)
            if reference.startswith(("http://", "https://", "#")):
                continue
            found.append((document, reference))
    return found


def test_every_referenced_media_file_is_present():
    missing = [
        f"{document.relative_to(ROOT)} -> {reference}"
        for document, reference in _referenced()
        if not (document.parent / reference).resolve().exists()
    ]
    assert not missing, missing


def test_the_demonstration_page_offers_both_caption_tracks():
    page = (ROOT / "docs" / "demo" / "index.html").read_text(encoding="utf-8")
    assert page.count("<track") == 2
    assert "pt-BR.vtt" in page and "en.vtt" in page


def test_the_readme_carries_every_section_the_artifact_committee_requires():
    """All ten sections are mandatory; a missing one costs the availability badge.

    The reviewer's first finding was exactly this: the README did not follow the
    template, so eight of the required sections were absent.
    """
    import re

    required = (
        "Estrutura do readme.md",
        "Selos Considerados",
        "Informações básicas",
        "Dependências",
        "Preocupações com segurança",
        "Instalação",
        "Teste mínimo",
        "Experimentos",
        "LICENSE",
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    missing = [
        section
        for section in required
        if not re.search(rf"^#+\s*{re.escape(section)}\s*$", readme, re.MULTILINE | re.IGNORECASE)
    ]
    assert not missing, missing


def test_the_dependency_table_matches_the_pinned_requirements():
    """Hand-written versions go stale; this table is generated from the lockfile."""
    import re

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    frozen = (ROOT / "requirements-frozen.txt").read_text(encoding="utf-8")
    table = re.search(
        r"<!-- dependency-table:start -->(.*?)<!-- dependency-table:end -->", readme, re.DOTALL
    )
    assert table, "the dependency table markers are gone"

    wrong = []
    for name, version in re.findall(r"\|\s*`([\w-]+)`\s*\|\s*([\d.]+)\s*\|", table.group(1)):
        if not re.search(
            rf"^{re.escape(name)}=={re.escape(version)}\b", frozen, re.MULTILINE | re.IGNORECASE
        ):
            wrong.append(f"{name}=={version}")
    assert not wrong, wrong


def test_the_readme_states_the_real_test_count():
    """The Experimentos section promises an exact number a reviewer will see."""
    import re
    import subprocess
    import sys

    collected = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--collect-only"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    total = int(re.search(r"(\d+) tests? collected", collected.stdout).group(1))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"`{total} passed`" in readme, f"the README does not promise {total} passed"
    assert f"{total} testes automatizados" in readme
