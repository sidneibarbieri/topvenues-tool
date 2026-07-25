"""Baselines and operating points for the scientific-readiness filter.

This experiment answers the two questions a careful reviewer asks about the
readiness result:

  1. Is prior top-tier authorship a real signal, or just a proxy for
     publication volume or community membership? We compare it against a
     prolific-author baseline, an any-security-venue baseline, and a random
     security-author control.
  2. Which author carries the signal? We re-run the same filter restricted to
     the first author and to the senior (last) author, exposing a tunable
     precision-recall trade-off.

It reads the configured publication scope and the versioned snapshot, runs
offline in a few seconds, and reuses :func:`src.readiness.analyze` for every
row by feeding it the cohort projected onto the relevant author position.
"""

from __future__ import annotations

import argparse
import random
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.arxiv_fetcher import ARXIV_ACKNOWLEDGMENT, load_jsonl
from src.config import activate_profile
from src.profiles import PROFILE_IDS, PROJECT_ROOT, select_profile_id, verified_profile_snapshot
from src.readiness import (
    OutcomeIndex,
    ReadinessResult,
    analyze,
    build_prior_author_set,
    strict_author_key,
)

THRESHOLD = 0.6
PROLIFIC_MIN_PAPERS = 3
RANDOM_SEED = 42

Cohort = list[tuple[str, tuple[str, ...]]]


def _author_lists(
    conn: sqlite3.Connection, events: tuple[str, ...] | None, lo: int, hi: int
) -> list[list[str]]:
    if events is None:
        rows = conn.execute(
            "SELECT authors FROM papers WHERE year BETWEEN ? AND ? AND authors IS NOT NULL",
            (lo, hi),
        ).fetchall()
    else:
        placeholders = ",".join("?" * len(events))
        rows = conn.execute(
            f"SELECT authors FROM papers WHERE event IN ({placeholders}) "
            f"AND year BETWEEN ? AND ? AND authors IS NOT NULL",
            (*events, lo, hi),
        ).fetchall()
    return [[a.strip() for a in r[0].split(",") if a.strip()] for r in rows]


def _scope_titles(conn: sqlite3.Connection, events: tuple[str, ...], lo: int, hi: int) -> list[str]:
    placeholders = ",".join("?" * len(events))
    rows = conn.execute(
        f"SELECT title FROM papers WHERE event IN ({placeholders}) "
        f"AND year BETWEEN ? AND ? AND title IS NOT NULL",
        (*events, lo, hi),
    ).fetchall()
    return [r[0] for r in rows]


def _prolific_authors(author_lists: list[list[str]], minimum: int) -> frozenset[str]:
    counts: Counter[str] = Counter()
    for authors in author_lists:
        for key in {strict_author_key(a) for a in authors if strict_author_key(a)}:
            counts[key] += 1
    return frozenset(key for key, count in counts.items() if count >= minimum)


def _project(cohort: Cohort, position: int) -> Cohort:
    """Keep only the author at ``position`` so ``analyze`` tests that slot."""
    return [(title, (authors[position],)) for title, authors in cohort if authors]


def _row(label: str, result: ReadinessResult) -> str:
    # RR (relative risk) vs. the excluded set; lift vs. population prevalence.
    # Raw flagged/hit counts make each row independently verifiable.
    relative_risk = f"{result.relative_risk:.1f}x" if result.base_rate else "inf"
    return (
        f"  {label:<26}{result.precision * 100:>7.1f}%{result.recall * 100:>7.0f}%"
        f"{relative_risk:>7}{result.lift:>6.1f}x{result.volume_reduction * 100:>7.0f}%"
        f"   [{result.converted_with}/{result.n_with_track_record}]"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        choices=PROFILE_IDS,
        default=select_profile_id(),
        help="immutable corpus profile (default: TOPVENUES_PROFILE or submitted-11)",
    )
    args = parser.parse_args()
    activate_profile(args.profile, PROJECT_ROOT)

    with verified_profile_snapshot(
        args.profile,
        PROJECT_ROOT,
        verify_preprints=True,
    ) as verified:
        profile = verified.profile
        scope = profile.configuration.study_scope
        core_events = tuple(scope.core_events)
        cohort_year = max(scope.prior_windows)
        prior_lo, prior_hi = scope.prior_windows[cohort_year]
        outcome_lo, outcome_hi = scope.outcome_windows[cohort_year]

        uri = f"file:{verified.database_path.resolve()}?mode=ro&immutable=1"
        with sqlite3.connect(uri, uri=True) as conn:
            top4 = build_prior_author_set(_author_lists(conn, core_events, prior_lo, prior_hi))
            any_corpus = build_prior_author_set(_author_lists(conn, None, prior_lo, prior_hi))
            prolific = _prolific_authors(
                _author_lists(conn, None, prior_lo, prior_hi),
                PROLIFIC_MIN_PAPERS,
            )
            outcome = OutcomeIndex(_scope_titles(conn, core_events, outcome_lo, outcome_hi))

        random.seed(RANDOM_SEED)
        random_authors = frozenset(random.sample(sorted(any_corpus), len(top4)))
        cohort: Cohort = [
            (p.title, p.authors)
            for p in load_jsonl(profile.preprint_snapshot_path)
            if p.submitted_at.startswith(str(cohort_year))
        ]

    print()
    print(
        f"  Scientific-readiness baselines ({cohort_year} cs.CR preprints, "
        f"Jaccard {THRESHOLD}, profile {profile.profile_id})"
    )
    print(
        f"  {'filter':<26}{'precision':>7}{'recall':>7}{'RR':>7}{'lift':>7} {'vol-cut':>7}"
        f"   [hit/flagged]"
    )
    print("  prestige vs. trivial signals")
    print(_row("prior top-4 (any author)", analyze(cohort, top4, outcome, THRESHOLD)))
    print(_row("any security-venue author", analyze(cohort, any_corpus, outcome, THRESHOLD)))
    print(
        _row(
            f"prolific (>= {PROLIFIC_MIN_PAPERS} papers)",
            analyze(cohort, prolific, outcome, THRESHOLD),
        )
    )
    print(_row("random security authors", analyze(cohort, random_authors, outcome, THRESHOLD)))
    print("  operating points by author position (prior top-4)")
    print(_row("first author", analyze(_project(cohort, 0), top4, outcome, THRESHOLD)))
    print(_row("senior (last) author", analyze(_project(cohort, -1), top4, outcome, THRESHOLD)))

    print(f"\n  {ARXIV_ACKNOWLEDGMENT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
