"""Top-4 concentration must rank by share and refuse thin evidence."""

from __future__ import annotations

import pytest

from src.analytics import (
    CONCENTRATION_MINIMUM_PAPERS,
    TOP4_CONCENTRATION_METRIC,
    _author_sort_key,
    top4_concentration,
)


def _entry(author: str, papers: int, top4: int) -> dict:
    return {"author": author, "papers": papers, "top4": top4, "score": 0.0}


def test_share_is_top4_over_papers():
    assert top4_concentration(_entry("a", 40, 30)) == pytest.approx(0.75)


def test_an_author_with_no_papers_scores_zero_instead_of_dividing():
    assert top4_concentration(_entry("a", 0, 0)) == 0.0


def test_concentration_outranks_volume():
    """A 38/38 author must beat a 95/78 one, which paper count cannot express."""
    focused = _entry("focused", 38, 38)
    prolific = _entry("prolific", 95, 78)
    ordered = sorted(
        [prolific, focused],
        key=lambda entry: _author_sort_key(entry, TOP4_CONCENTRATION_METRIC),
    )
    assert ordered[0]["author"] == "focused"


def test_ties_on_share_break_towards_the_larger_body_of_work():
    small = _entry("small", 12, 12)
    large = _entry("large", 38, 38)
    ordered = sorted(
        [small, large],
        key=lambda entry: _author_sort_key(entry, TOP4_CONCENTRATION_METRIC),
    )
    assert ordered[0]["author"] == "large"


def test_the_minimum_is_high_enough_to_exclude_single_paper_authors():
    """One top-4 paper scores 100%; without a floor that noise wins the ranking."""
    assert CONCENTRATION_MINIMUM_PAPERS >= 5
