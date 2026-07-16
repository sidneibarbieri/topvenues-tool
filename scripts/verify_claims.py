"""Assert that the released artifact matches the paper's headline claims."""

import sqlite3
import sys

EXPECTED_PAPERS = 144785
EXPECTED_ABSTRACTS = 17603
EXPECTED_BIBTEX = 144785


def main() -> int:
    conn = sqlite3.connect("data/dataset/papers.db")
    try:
        total = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        with_abstract = conn.execute(
            "SELECT COUNT(*) FROM papers WHERE abstract IS NOT NULL AND abstract != ''"
        ).fetchone()[0]
        with_bibtex = conn.execute(
            "SELECT COUNT(*) FROM papers WHERE bibtex IS NOT NULL AND bibtex != ''"
        ).fetchone()[0]
    finally:
        conn.close()

    checks = (
        ("papers", total, EXPECTED_PAPERS),
        ("abstracts", with_abstract, EXPECTED_ABSTRACTS),
        ("bibtex", with_bibtex, EXPECTED_BIBTEX),
    )
    failures = [name for name, actual, expected in checks if actual != expected]

    for name, actual, expected in checks:
        mark = "ok " if actual == expected else "FAIL"
        print(f"  {mark} {name:<10} {actual:>5} (expected {expected})")

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
