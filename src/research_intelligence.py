"""Transparent researcher-surveillance analytics over a frozen corpus."""

from __future__ import annotations

import collections
import re
import sqlite3
from pathlib import Path
from urllib.parse import urlencode

from pydantic import BaseModel, Field

from src.analytics import _split_authors
from src.areas import area_for
from src.tiers import tier_for


class EmergingResearcher(BaseModel):
    """Observed publication-rate change, not a prediction of scientific impact."""

    author: str
    papers: int
    recent_papers: int
    prior_papers: int
    recent_rate: float
    prior_rate: float
    rate_change: float
    recent_since: int
    through_year: int
    first_year: int
    last_year: int


class TrajectoryPoint(BaseModel):
    year: int
    papers: int
    first_author_papers: int
    last_author_papers: int
    venues: list[str] = Field(default_factory=list)


class Collaboration(BaseModel):
    collaborator: str
    joint_papers: int
    first_year: int
    last_year: int
    venues: list[str] = Field(default_factory=list)


class ResearchWatchlist(BaseModel):
    """Portable, local watch definition with no account or telemetry."""

    schema_version: str = "1.0"
    profile_id: str
    name: str
    authors: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    tier_scope: str = "All declared venues"
    known_paper_ids: list[str] = Field(default_factory=list)


def _paper_rows(
    db_path: Path,
    *,
    topic: str | None = None,
    area: str | None = None,
    allowed_tiers: frozenset[str] | None = None,
) -> list[tuple[str, str, int]]:
    sql = "SELECT authors, event, year FROM papers WHERE authors IS NOT NULL AND year IS NOT NULL"
    params: list[str] = []
    if topic:
        sql += " AND (title LIKE ? OR abstract LIKE ?)"
        pattern = f"%{topic}%"
        params.extend([pattern, pattern])
    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(sql, params).fetchall()
    return [
        (authors, event, int(year))
        for authors, event, year in rows
        if (area is None or area_for(event) == area)
        and (allowed_tiers is None or tier_for(event) in allowed_tiers)
    ]


def emerging_researchers(
    db_path: Path,
    *,
    topic: str | None = None,
    area: str | None = None,
    allowed_tiers: frozenset[str] | None = None,
    recent_years: int = 3,
    minimum_recent_papers: int = 2,
    limit: int = 20,
) -> list[EmergingResearcher]:
    """Rank observed increases in annual publication rate.

    The recent window is compared with all earlier years in the selected corpus.
    ``rate_change`` is recent papers/year minus prior papers/year. It is a descriptive
    signal within the corpus, not a forecast or an impact metric.
    """
    if recent_years < 1:
        raise ValueError("recent_years must be positive")
    rows = _paper_rows(db_path, topic=topic, area=area, allowed_tiers=allowed_tiers)
    if not rows:
        return []
    min_year = min(year for _, _, year in rows)
    max_year = max(year for _, _, year in rows)
    recent_since = max(min_year, max_year - recent_years + 1)
    recent_span = max_year - recent_since + 1
    prior_span = recent_since - min_year

    counts: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    years: dict[str, list[int]] = collections.defaultdict(list)
    for raw_authors, _, year in rows:
        for author in set(_split_authors(raw_authors)):
            period = "recent" if year >= recent_since else "prior"
            counts[author][period] += 1
            years[author].append(year)

    signals: list[EmergingResearcher] = []
    for author, periods in counts.items():
        recent = periods["recent"]
        if recent < minimum_recent_papers:
            continue
        prior = periods["prior"]
        recent_rate = recent / recent_span
        prior_rate = prior / prior_span if prior_span else 0.0
        signals.append(
            EmergingResearcher(
                author=author,
                papers=recent + prior,
                recent_papers=recent,
                prior_papers=prior,
                recent_rate=round(recent_rate, 2),
                prior_rate=round(prior_rate, 2),
                rate_change=round(recent_rate - prior_rate, 2),
                recent_since=recent_since,
                through_year=max_year,
                first_year=min(years[author]),
                last_year=max(years[author]),
            )
        )
    return sorted(
        signals,
        key=lambda item: (-item.rate_change, -item.recent_papers, item.author),
    )[:limit]


def researcher_trajectory(db_path: Path, author: str) -> list[TrajectoryPoint]:
    """Return annual evidence for one exact DBLP author identity."""
    by_year: dict[int, dict[str, object]] = {}
    for raw_authors, event, year in _paper_rows(db_path):
        authors = _split_authors(raw_authors)
        if author not in authors:
            continue
        entry = by_year.setdefault(
            year,
            {"papers": 0, "first": 0, "last": 0, "venues": collections.Counter()},
        )
        entry["papers"] = int(entry["papers"]) + 1
        entry["first"] = int(entry["first"]) + int(authors[0] == author)
        entry["last"] = int(entry["last"]) + int(authors[-1] == author)
        venue_counts = entry["venues"]
        assert isinstance(venue_counts, collections.Counter)
        venue_counts[event] += 1
    return [
        TrajectoryPoint(
            year=year,
            papers=int(entry["papers"]),
            first_author_papers=int(entry["first"]),
            last_author_papers=int(entry["last"]),
            venues=[venue for venue, _ in entry["venues"].most_common()],
        )
        for year, entry in sorted(by_year.items())
    ]


def collaboration_network(db_path: Path, author: str, *, limit: int = 20) -> list[Collaboration]:
    """Return direct coauthors for one exact DBLP identity."""
    stats: dict[str, dict[str, object]] = {}
    for raw_authors, event, year in _paper_rows(db_path):
        authors = _split_authors(raw_authors)
        if author not in authors:
            continue
        for collaborator in set(authors) - {author}:
            entry = stats.setdefault(
                collaborator,
                {"papers": 0, "years": [], "venues": collections.Counter()},
            )
            entry["papers"] = int(entry["papers"]) + 1
            entry["years"].append(year)
            entry["venues"][event] += 1
    result = [
        Collaboration(
            collaborator=collaborator,
            joint_papers=int(entry["papers"]),
            first_year=min(entry["years"]),
            last_year=max(entry["years"]),
            venues=[venue for venue, _ in entry["venues"].most_common(3)],
        )
        for collaborator, entry in stats.items()
    ]
    return sorted(result, key=lambda item: (-item.joint_papers, item.collaborator))[:limit]


def arxiv_author_search_url(author: str) -> str:
    """Build an external search URL without claiming cross-source identity resolution."""
    external_name = re.sub(r"\s+\d{4}$", "", author).strip()
    query = f'au:"{external_name}"'
    return "https://arxiv.org/search/?" + urlencode(
        {"query": query, "searchtype": "all", "abstracts": "show", "order": "-announced_date_first"}
    )


def watchlist_matching_ids(db_path: Path, watchlist: ResearchWatchlist) -> list[str]:
    """Return paper IDs matching any watched exact author or topic."""
    from src.tiers import tiers_in_scope

    allowed_tiers = tiers_in_scope(watchlist.tier_scope)
    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT paper_id, authors, title, abstract, event FROM papers"
        ).fetchall()
    watched_authors = set(watchlist.authors)
    watched_topics = [topic.casefold() for topic in watchlist.topics if topic.strip()]
    matches: list[str] = []
    for paper_id, raw_authors, title, abstract, event in rows:
        if allowed_tiers is not None and tier_for(event) not in allowed_tiers:
            continue
        author_match = bool(watched_authors & set(_split_authors(raw_authors)))
        searchable = f"{title or ''}\n{abstract or ''}".casefold()
        topic_match = any(topic in searchable for topic in watched_topics)
        if author_match or topic_match:
            matches.append(paper_id)
    return sorted(matches)


def unseen_watchlist_matches(db_path: Path, watchlist: ResearchWatchlist) -> list[str]:
    """Compare a watchlist baseline with another frozen or refreshed profile."""
    known = set(watchlist.known_paper_ids)
    return [
        paper_id for paper_id in watchlist_matching_ids(db_path, watchlist) if paper_id not in known
    ]
