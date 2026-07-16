#!/usr/bin/env python3
"""Report how many curated award papers appear in the topVenues corpus.

Loads every ``data/awards/*_paper_awards.json`` table, joins it to the corpus by
normalized title within venue, prints per-venue coverage, and writes the matched
pairs to ``data/awards/award_corpus_matches.tsv``. Unmatched awards are reported
honestly: the corpus may not yet contain that paper for that venue/year.
"""

from __future__ import annotations

import collections
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.awards import load_award_records, match_awards_to_corpus  # noqa: E402

AWARDS_DIR = REPO_ROOT / "data" / "awards"
DB_PATH = REPO_ROOT / "data" / "dataset" / "papers.db"
MATCHES_TSV = AWARDS_DIR / "award_corpus_matches.tsv"
MATCH_FIELDS = ("venue", "year", "award", "title", "paper_id", "source_url")


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(
            f"corpus DB missing: {DB_PATH} (run `python3 -m src.cli refresh-db` first)"
        )

    records = load_award_records(AWARDS_DIR)
    if not records:
        raise SystemExit(f"no award tables found under {AWARDS_DIR}")

    matched, unmatched = match_awards_to_corpus(records, DB_PATH)

    by_venue: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])
    for match in matched:
        by_venue[match.award.venue][0] += 1
    for record in unmatched:
        by_venue[record.venue][1] += 1

    print(f"award records: {len(records)} | matched in corpus: {len(matched)} | "
          f"unmatched: {len(unmatched)}")
    print(f"{'venue':<18}{'matched':>9}{'unmatched':>11}")
    for venue in sorted(by_venue):
        hit, miss = by_venue[venue]
        print(f"{venue:<18}{hit:>9}{miss:>11}")

    with MATCHES_TSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(MATCH_FIELDS)
        for match in matched:
            award = match.award
            writer.writerow([award.venue, award.year, award.award, award.title,
                             match.paper_id, award.source_url])
    print(f"wrote {len(matched)} matches -> {MATCHES_TSV.name}")

    if unmatched:
        print("\nunmatched (not in corpus by title+venue):")
        for record in unmatched:
            print(f"  [{record.venue} {record.year}] {record.title}")


if __name__ == "__main__":
    main()
