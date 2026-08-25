"""Lock the chart design decisions that integrations have silently dropped.

Visual regressions do not fail a test suite by themselves, so each of these
decisions was lost at least once during a branch integration and only found by
re-rendering the interface. These assertions make the loss fail in CI instead.
"""

from __future__ import annotations

import pandas as pd

from web import charts


def _sample(rows: int) -> pd.DataFrame:
    return pd.DataFrame(
        {"Venue": [f"venue {index}" for index in range(rows)], "Papers": range(rows, 0, -1)}
    )


def test_bars_declare_one_thickness_for_the_whole_application():
    """A 20-bar chart beside an 8-bar chart must not draw different bars."""
    assert isinstance(charts.BAR_THICKNESS, int)
    chart = charts.bar_chart(_sample(6), "Venue", "Papers", charts.alt.selection_point())
    bar_layer = chart.to_dict()["layer"][0]
    assert bar_layer["mark"]["size"] == charts.BAR_THICKNESS


def test_horizontal_height_grows_with_the_bar_count():
    """Otherwise thickness silently shrinks as categories are added."""
    small = charts.bar_chart(_sample(4), "Venue", "Papers", charts.alt.selection_point())
    large = charts.bar_chart(_sample(20), "Venue", "Papers", charts.alt.selection_point())
    assert large.to_dict()["height"] > small.to_dict()["height"]


def test_every_bar_carries_its_value():
    """A dashboard read at a glance must not require hovering to learn a number."""
    chart = charts.bar_chart(_sample(5), "Venue", "Papers", charts.alt.selection_point())
    layers = chart.to_dict()["layer"]
    assert any(layer["mark"]["type"] == "text" for layer in layers)


def test_the_palette_is_declared_in_one_place():
    """Hex literals at call sites are how the palette drifted before."""
    for name in ("ACCENT", "COVERAGE", "SERIES", "INK", "MUTED"):
        assert hasattr(charts, name), f"{name} must be declared in web/charts.py"


def test_unselected_bars_read_as_clearly_dimmed():
    """A subtle difference makes the click-to-filter affordance invisible."""
    assert charts.UNSELECTED_OPACITY <= 0.5
