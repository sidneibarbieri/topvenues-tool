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
