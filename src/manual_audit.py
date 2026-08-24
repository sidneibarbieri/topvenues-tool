"""Deterministic sampling and validation for a human abstract-quality audit."""

from __future__ import annotations

import hashlib
import math
import sqlite3
from pathlib import Path

import pandas as pd
from pydantic import BaseModel

AUDIT_LABELS = ("label_complete", "label_uncontaminated", "label_matches_paper")


class AuditSummary(BaseModel):
    sampled: int
    labelled: int
    usable: int
    usable_rate: float | None
    ci95_low: float | None
    ci95_high: float | None


def _allocation(counts: dict[str, int], sample_size: int) -> dict[str, int]:
    """Proportional venue allocation using deterministic largest remainders."""
    total = sum(counts.values())
    if sample_size > total:
        raise ValueError("sample_size exceeds corpus size")
    exact = {venue: sample_size * count / total for venue, count in counts.items()}
    allocated = {venue: int(value) for venue, value in exact.items()}
    remaining = sample_size - sum(allocated.values())
    order = sorted(counts, key=lambda venue: (-(exact[venue] - allocated[venue]), venue))
    for venue in order[:remaining]:
        allocated[venue] += 1
    return allocated


def build_audit_sample(
    db_path: Path, *, sample_size: int = 200, seed: str = "security-20-v3-audit-1"
) -> pd.DataFrame:
    """Create a reproducible venue-stratified sample of corpus records."""
    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT paper_id, event, year, title, ee, abstract FROM papers ORDER BY paper_id"
        ).fetchall()
    counts: dict[str, int] = {}
    for _, event, *_ in rows:
        counts[event] = counts.get(event, 0) + 1
    allocated = _allocation(counts, sample_size)
    by_venue: dict[str, list[tuple]] = {venue: [] for venue in counts}
    for row in rows:
        by_venue[row[1]].append(row)

    selected: list[tuple] = []
    for venue, venue_rows in by_venue.items():
        ranked = sorted(
            venue_rows,
            key=lambda row: hashlib.sha256(f"{seed}\0{row[0]}".encode()).hexdigest(),
        )
        selected.extend(ranked[: allocated[venue]])
    selected.sort(key=lambda row: (row[1], row[0]))
    return pd.DataFrame(
        [
            {
                "sample_id": index,
                "paper_id": paper_id,
                "venue": event,
                "year": year,
                "title": title,
                "source_url": ee or "",
                "abstract_present": bool(abstract and abstract.strip()),
                "abstract": abstract or "",
                "label_complete": "",
                "label_uncontaminated": "",
                "label_matches_paper": "",
                "reviewer": "",
                "notes": "",
            }
            for index, (paper_id, event, year, title, ee, abstract) in enumerate(selected, start=1)
        ]
    )


def _as_label(value: object) -> bool | None:
    normalized = str(value).strip().casefold()
    if normalized in {"true", "yes", "1", "y"}:
        return True
    if normalized in {"false", "no", "0", "n"}:
        return False
    return None


def _wilson_interval(successes: int, total: int) -> tuple[float, float]:
    z = 1.959963984540054
    proportion = successes / total
    denominator = 1 + z**2 / total
    centre = (proportion + z**2 / (2 * total)) / denominator
    margin = (
        z * math.sqrt(proportion * (1 - proportion) / total + z**2 / (4 * total**2)) / denominator
    )
    return centre - margin, centre + margin


def summarize_audit(frame: pd.DataFrame) -> AuditSummary:
    """Summarize fully labelled rows; incomplete rows are never silently imputed."""
    missing_columns = set(AUDIT_LABELS) - set(frame.columns)
    if missing_columns:
        raise ValueError(f"missing audit columns: {sorted(missing_columns)}")
    labelled = 0
    usable = 0
    for _, row in frame.iterrows():
        labels = [_as_label(row[column]) for column in AUDIT_LABELS]
        if any(label is None for label in labels):
            continue
        labelled += 1
        usable += int(all(labels))
    if labelled == 0:
        return AuditSummary(
            sampled=len(frame),
            labelled=0,
            usable=0,
            usable_rate=None,
            ci95_low=None,
            ci95_high=None,
        )
    low, high = _wilson_interval(usable, labelled)
    return AuditSummary(
        sampled=len(frame),
        labelled=labelled,
        usable=usable,
        usable_rate=round(usable / labelled, 4),
        ci95_low=round(low, 4),
        ci95_high=round(high, 4),
    )
