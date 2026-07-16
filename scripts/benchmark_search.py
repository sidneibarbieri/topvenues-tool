#!/usr/bin/env python3
"""Benchmark both search paths with a warm-up and repeated timed trials."""

from __future__ import annotations

import argparse
import sqlite3
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager

TERMS = ("machine learning", "fuzzing", "intrusion detection", "ransomware")


def _elapsed_ms(callable_) -> tuple[float, list]:
    start = time.perf_counter()
    rows = callable_()
    return (time.perf_counter() - start) * 1000, rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("data/dataset/papers.db"))
    parser.add_argument("--trials", type=int, default=11)
    args = parser.parse_args()
    if args.trials < 3:
        parser.error("--trials must be at least 3")

    db = DatabaseManager(args.db)
    started = time.perf_counter()
    db.build_fts_index()
    print(f"FTS5 index build: {time.perf_counter() - started:.2f} s")

    with sqlite3.connect(args.db) as connection:
        for term in TERMS:
            pattern = f"%{term}%"

            def substring_search(pattern: str = pattern) -> list:
                return connection.execute(
                    "SELECT paper_id FROM papers "
                    "WHERE title LIKE ? OR abstract LIKE ?",
                    (pattern, pattern),
                ).fetchall()

            def ranked_search(term: str = term) -> list:
                return db.search_ranked(term, limit=None)

            # Untimed warm-up faults relevant pages into the OS and SQLite caches.
            substring_search()
            ranked_search()

            substring_times: list[float] = []
            ranked_times: list[float] = []
            substring_rows: list = []
            ranked_rows: list = []
            for _ in range(args.trials):
                elapsed, substring_rows = _elapsed_ms(substring_search)
                substring_times.append(elapsed)
                elapsed, ranked_rows = _elapsed_ms(ranked_search)
                ranked_times.append(elapsed)

            print(
                f"{term:<22} "
                f"LIKE {len(substring_rows):>5} {statistics.median(substring_times):>6.1f} ms  "
                f"BM25 {len(ranked_rows):>5} {statistics.median(ranked_times):>6.1f} ms"
            )
            if not substring_rows or not ranked_rows:
                raise SystemExit(f"search returned no results for {term!r}")


if __name__ == "__main__":
    main()
