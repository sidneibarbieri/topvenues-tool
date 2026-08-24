"""Area-level analytics over the corpus: trends, prominent authors, award standouts.

Built on the deterministic venue-to-area registry (``areas.py``). Authors are parsed
from the stored author string; an author's per-area counts reflect the venues they
publish in. These functions support literature-review work: which areas are growing,
who the prominent authors are, and which papers were recognized with awards.
"""

from __future__ import annotations

import collections
import re
import sqlite3
from pathlib import Path

from src.areas import area_for
from src.awards import AwardMatch, load_award_records, match_awards_to_corpus
from src.tiers import TOP4, TOP4_REGIONAL, TOP_TIER, tier_for, weight_for

_AUTHOR_SPLIT = re.compile(r"\s*,\s*|\s+and\s+")
AUTHOR_POSITIONS = ("any", "first", "last")


def _split_authors(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [
        # Keep DBLP's numeric suffix. It distinguishes homonyms; removing it
        # silently merges different people and invalidates author rankings.
        name.strip()
        for name in _AUTHOR_SPLIT.split(raw)
        if name.strip()
    ]


def _authors_at_position(raw: str | None, position: str) -> list[str]:
    """Return identities for one declared authorship-position view."""
    if position not in AUTHOR_POSITIONS:
        raise ValueError(f"unknown author position {position!r}")
    authors = _split_authors(raw)
    if position == "any":
        return authors
    if not authors:
        return []
    return [authors[0] if position == "first" else authors[-1]]


def area_year_counts(db_path: Path) -> dict[str, dict[int, int]]:
    """Papers per area per year: ``{area: {year: count}}`` (trend signal)."""
    counts: dict[str, dict[int, int]] = collections.defaultdict(
        lambda: collections.defaultdict(int)
    )
    connection = sqlite3.connect(db_path)
    try:
        for event, year in connection.execute(
            "select event, year from papers where year is not null"
        ):
            counts[area_for(event)][int(year)] += 1
    finally:
        connection.close()
    return {area: dict(sorted(years.items())) for area, years in counts.items()}


def top_authors(
    db_path: Path, area: str | None = None, limit: int = 15
) -> list[tuple[str, int]]:
    """Most prolific authors, optionally restricted to a single area."""
    counter: collections.Counter[str] = collections.Counter()
    connection = sqlite3.connect(db_path)
    try:
        for authors, event in connection.execute("select authors, event from papers"):
            if area is not None and area_for(event) != area:
                continue
            counter.update(_split_authors(authors))
    finally:
        connection.close()
    return counter.most_common(limit)


def reference_authors(
    db_path: Path,
    topic: str | None = None,
    area: str | None = None,
    limit: int = 20,
    awards_dir: Path | None = None,
    position: str = "any",
) -> list[dict]:
    """Tier-weighted ranking of the reference authors for a topic or area.

    A raw publication count treats a workshop paper and an IEEE S&P paper as
    equal; this ranking does not. Each paper contributes its venue-tier weight
    (``tiers.WEIGHT_BY_TIER``) to every listed author, so recurring top-tier
    names dominate the list. The optional ``topic`` restricts scope with a
    case-insensitive match over title and abstract; ``area`` restricts by the
    venue-to-area registry. Deterministic: ties break by top-4 count, paper
    count, then name.

    This is a corpus-visibility heuristic, not a citation/quality/authority
    metric. Each entry exposes the evidence used by the heuristic so users do
    not have to interpret an opaque score.
    """
    if position not in AUTHOR_POSITIONS:
        raise ValueError(f"unknown author position {position!r}")
    sql = "select paper_id, authors, event, year from papers where authors is not null"
    params: list = []
    if topic:
        sql += " and (title like ? or abstract like ?)"
        pattern = f"%{topic}%"
        params.extend([pattern, pattern])

    awarded_ids: set[str] = set()
    if awards_dir is not None and awards_dir.exists():
        matched, _ = match_awards_to_corpus(load_award_records(awards_dir), db_path)
        awarded_ids = {match.paper_id for match in matched}

    stats: dict[str, dict] = {}
    connection = sqlite3.connect(db_path)
    try:
        for paper_id, authors, event, year in connection.execute(sql, params):
            if area is not None and area_for(event) != area:
                continue
            tier = tier_for(event)
            weight = weight_for(tier)
            for author in _authors_at_position(authors, position):
                entry = stats.setdefault(author, {
                    "author": author,
                    "score": 0.0,
                    "papers": 0,
                    "top4": 0,
                    "top_tier": 0,
                    "top4_regional": 0,
                    "awards": 0,
                    "first_year": year,
                    "last_year": year,
                    "_venues": collections.Counter(),
                })
                entry["score"] += weight
                entry["papers"] += 1
                if tier == TOP4:
                    entry["top4"] += 1
                elif tier == TOP_TIER:
                    entry["top_tier"] += 1
                elif tier == TOP4_REGIONAL:
                    entry["top4_regional"] += 1
                if paper_id in awarded_ids:
                    entry["awards"] += 1
                if year is not None:
                    entry["first_year"] = min(entry["first_year"] or year, year)
                    entry["last_year"] = max(entry["last_year"] or year, year)
                if event:
                    entry["_venues"][event] += 1
    finally:
        connection.close()

    ranked = sorted(
        stats.values(),
        key=lambda e: (-e["score"], -e["top4"], -e["papers"], e["author"]),
    )[:limit]
    for entry in ranked:
        entry["venues"] = [venue for venue, _ in entry.pop("_venues").most_common(3)]
        entry["score"] = round(entry["score"], 1)
    return ranked


def topic_trend(
    db_path: Path,
    topic: str,
    area: str | None = None,
    year_start: int | None = None,
) -> dict:
    """Yearly volume and corpus share for a topic, plus its main venues.

    Answers two review questions at once: "is this topic growing?" and
    "where does it get published?". The topic matches title and abstract
    case-insensitively. ``share_pct`` normalizes each year's topic count by
    that year's corpus size (within the same ``area`` scope), so a growing
    corpus does not masquerade as a growing topic. Abstracts exist only where
    the curation policy backfills them, so counts are a lower bound for
    venues outside the enriched layers.
    """
    pattern = f"%{topic}%"
    matched_by_year: dict[int, int] = collections.defaultdict(int)
    total_by_year: dict[int, int] = collections.defaultdict(int)
    venue_counter: collections.Counter[str] = collections.Counter()

    connection = sqlite3.connect(db_path)
    try:
        rows = connection.execute(
            "select event, year, (title like ? or abstract like ?) as matched "
            "from papers where year is not null",
            (pattern, pattern),
        )
        for event, year, matched in rows:
            if area is not None and area_for(event) != area:
                continue
            year = int(year)
            if year_start is not None and year < year_start:
                continue
            total_by_year[year] += 1
            if matched:
                matched_by_year[year] += 1
                if event:
                    venue_counter[event] += 1
    finally:
        connection.close()

    by_year = [
        {
            "year": year,
            "papers": matched_by_year.get(year, 0),
            "share_pct": round(100.0 * matched_by_year.get(year, 0) / total, 2),
        }
        for year, total in sorted(total_by_year.items())
    ]
    return {
        "topic": topic,
        "total": sum(matched_by_year.values()),
        "by_year": by_year,
        "top_venues": venue_counter.most_common(5),
    }


def awarded_by_area(awards_dir: Path, db_path: Path) -> dict[str, list[AwardMatch]]:
    """Award-winning corpus papers grouped by research area."""
    matched, _ = match_awards_to_corpus(load_award_records(awards_dir), db_path)
    connection = sqlite3.connect(db_path)
    try:
        area_by_id = {
            paper_id: area_for(event)
            for paper_id, event in connection.execute(
                "select paper_id, event from papers"
            )
        }
    finally:
        connection.close()
    by_area: dict[str, list[AwardMatch]] = collections.defaultdict(list)
    for match in matched:
        by_area[area_by_id.get(match.paper_id, "unknown")].append(match)
    return dict(by_area)
