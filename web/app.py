"""Streamlit web interface for the bibliographic corpus explorer."""

import asyncio
import html
import sqlite3
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ARTIFACT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ARTIFACT_ROOT))

from src.abstract_fetcher import AbstractFetcher
from src.analytics import authors_at_position
from src.areas import area_for
from src.awards import build_corpus_award_map
from src.chart_interactions import selected_chart_value
from src.collector import Collector
from src.database import require_corpus
from src.models import PaperClass, SearchFilters
from src.tiers import tier_for, tier_scope_options, tiers_in_scope

PAGE_SIZE_OPTIONS = (25, 50, 100, 200)
ABSTRACT_PREVIEW_CHARS = 280

st.set_page_config(
    page_title="TopVenues - Security Paper Explorer",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Styles ────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
        :root {
            --ink:    #18212f;
            --navy:   #243247;
            --slate:  #3d4b5f;
            --teal:   #2f6f73;
            --amber:  #b36b2c;
            --green:  #4f7d4a;
            --rose:   #a84646;
            --muted:  #d8e2e3;
            --border: #d8dde3;
            --bg:     #f8f8f5;
            --card:   #ffffff;
        }

        .stApp, [data-testid="stAppViewContainer"] {
            background: var(--bg);
            color: var(--ink);
        }
        [data-testid="stHeader"] { background: rgba(248, 248, 245, .86); }
        [data-testid="stMainBlockContainer"] { padding-top: 2.2rem; }
        [data-testid="stDeployButton"],
        [data-testid="stAppDeployButton"],
        [data-testid="stToolbarActions"],
        [data-testid="stMainMenu"],
        #MainMenu,
        footer {
            visibility: hidden;
            height: 0;
        }
        [data-testid="stExpandSidebarButton"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapseButton"] * {
            visibility: visible !important;
        }

        .app-header {
            background: #eef4f5;
            border-left: 5px solid var(--teal);
            border-radius: 6px;
            padding: 1.35rem 1.6rem;
            margin-bottom: 1.4rem;
            border-top: 1px solid var(--border);
            border-right: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
        }
        .app-header h1 {
            color: #18212f !important; font-size: 1.75rem; font-weight: 700;
            margin: 0 0 .35rem; letter-spacing: 0;
        }
        .app-header p { color: #4d5f71; font-size: .96rem; margin: 0; }

        .metric-row { display: flex; gap: .9rem; margin-bottom: 1.2rem; flex-wrap: wrap; }
        .metric {
            flex: 1; min-width: 160px;
            background: var(--card); border: 1px solid var(--border);
            border-left: 4px solid var(--teal);
            border-radius: 6px; padding: .95rem 1.1rem;
        }
    .metric.amber { border-left-color: var(--amber); }
    .metric.green { border-left-color: var(--green); }
    .metric.rose  { border-left-color: var(--rose); }
    .metric .lbl { color: #6b7c8d; font-size: .72rem; text-transform: uppercase;
                   letter-spacing: .8px; margin-bottom: .35rem; }
        .metric .val { color: var(--ink); font-size: 1.7rem; font-weight: 700; line-height: 1; }
    .metric .sub { color: #8b97a3; font-size: .72rem; margin-top: .25rem; }

    .tag {
            display: inline-block; border-radius: 3px;
        padding: 2px 9px; font-size: .72rem; font-weight: 700;
        margin-right: 4px; letter-spacing: .3px;
    }
    .tag-sok      { background: #fff3cd; color: #7d5a00; }
    .tag-survey   { background: #d1ecf1; color: #0c5460; }
    .tag-poster   { background: #f8d7da; color: #721c24; }
    .tag-workshop { background: #e2d9f3; color: #3d2278; }
    .tag-short    { background: #e9ecef; color: #495057; }
    .tag-journal  { background: #d4edda; color: #155724; }
    .tag-article  { background: #f0f4f8; color: #0d1b2a; }

    section[data-testid="stSidebar"] {
        background: #f1f4f3;
        border-right: 1px solid var(--border);
    }
    section[data-testid="stSidebar"] * { color: var(--ink) !important; }
    section[data-testid="stSidebar"] h2 {
        color: var(--ink) !important; font-size: .95rem;
        letter-spacing: .4px; text-transform: uppercase;
        border-bottom: 1px solid var(--border);
        padding-bottom: .5rem; margin: .4rem 0 .8rem;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p {
        color: #334155 !important;
    }

        .results-bar {
            display: flex; align-items: center; justify-content: space-between;
            background: var(--bg); border: 1px solid var(--border); border-radius: 6px;
            padding: .7rem 1rem; margin-bottom: 1rem;
        }
        .results-bar .count { color: var(--ink); font-size: 1rem; font-weight: 700; }
    .results-bar .sub   { color: #6b7c8d; font-size: .85rem; }

        .paper-card {
            background: var(--card); border: 1px solid var(--border);
            border-radius: 6px; padding: 1.35rem 1.55rem; margin-top: 1rem;
        }
        .paper-card h3 { color: var(--ink); margin: 0 0 .6rem; }
    .paper-meta {
        display: flex; gap: 1.5rem; color: #6b7c8d; font-size: .85rem;
        margin-bottom: .8rem; flex-wrap: wrap;
    }
    .paper-abstract {
        white-space: pre-wrap; line-height: 1.6;
        color: #2c3e50; font-size: .95rem;
    }

        .claim-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: .8rem; margin: .9rem 0 1.2rem;
        }
        .claim {
            border: 1px solid var(--border); border-radius: 6px; background: var(--card);
            padding: .95rem 1rem;
        }
        .claim .name { color: #607084; text-transform: uppercase; font-size: .72rem; font-weight: 700; }
        .claim .value { color: var(--ink); font-size: 1.6rem; font-weight: 700; line-height: 1.2; }
        .claim .note { color: #637184; font-size: .84rem; }
        .stDataFrame { border-radius: 6px; overflow: hidden; }
        div[data-testid="stExpander"] { border-radius: 6px; }
    .footer {
        color: #94a3b8; font-size: .78rem; text-align: center;
        margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border);
    }
</style>
""",
    unsafe_allow_html=True,
)


# ── Helpers ────────────────────────────────────────────────────────────────


def _run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@st.cache_resource(show_spinner="Loading dataset…")
def _load_collector() -> Collector:
    """Open the corpus anchored at the artifact root, independent of the shell's
    working directory, and report a missing corpus instead of showing an empty one.
    """
    collector = Collector(base_dir=ARTIFACT_ROOT)
    require_corpus(collector.db.db_path, collector.db.snapshot_path)
    collector.papers = collector._load_papers_from_disk()
    return collector


@st.cache_data(show_spinner=False)
def _award_map() -> dict[str, list[str]]:
    """Cached map of corpus paper_id -> award labels (empty if no award tables)."""
    db_path = _load_collector().db.db_path
    awards_dir = db_path.parent.parent / "awards"
    if not awards_dir.exists():
        return {}
    return build_corpus_award_map(awards_dir, db_path)


@st.cache_data(show_spinner=False)
def _cached_topic_trend(
    db_path: str, topic: str, area: str | None, tier_scope: str
) -> dict:
    from src.analytics import topic_trend

    return topic_trend(
        Path(db_path), topic, area=area, allowed_tiers=tiers_in_scope(tier_scope)
    )


@st.cache_data(show_spinner=False)
def _cached_reference_authors(
    db_path: str, topic: str | None, area: str | None, position: str,
    tier_scope: str, ranking_metric: str, limit: int
) -> list[dict]:
    from src.analytics import reference_authors

    return reference_authors(
        Path(db_path), topic=topic, area=area, position=position, limit=limit,
        awards_dir=Path(db_path).parent.parent / "awards",
        allowed_tiers=tiers_in_scope(tier_scope),
        ranking_metric=ranking_metric,
    )


def _award_label(labels: list[str] | None) -> str:
    """Plain-text award label for the results table (no glyph, keeps sort/filter clean)."""
    return "; ".join(labels) if labels else ""


def _safe_html(value: object) -> str:
    if value is None:
        return "—"
    return html.escape(str(value), quote=True)


def _venue_options(
    collector: Collector, allowed_tiers: frozenset[str] | None = None
) -> list[str]:
    venues = sorted({
        paper.event
        for paper in collector.papers
        if paper.event and (allowed_tiers is None or tier_for(paper.event) in allowed_tiers)
    })
    return ["All venues", *venues]


def _abstract_length_predicate(papers, choice: str):
    if choice == "Any":
        return papers
    if choice == "Has abstract":
        return [paper for paper in papers if paper.abstract]
    if choice == "Missing abstract":
        return [paper for paper in papers if not paper.abstract]
    if choice == "Short (≤ 150 words)":
        return [paper for paper in papers if 0 < paper.abstract_words <= 150]
    if choice == "Medium (151–300 words)":
        return [paper for paper in papers if 151 <= paper.abstract_words <= 300]
    if choice == "Long (> 300 words)":
        return [paper for paper in papers if paper.abstract_words > 300]
    return papers


def _bibtex_predicate(papers, only_with_bibtex: bool):
    return [paper for paper in papers if paper.bibtex] if only_with_bibtex else papers


def _truncate(text: str | None, max_chars: int = ABSTRACT_PREVIEW_CHARS) -> str:
    if not text:
        return "—"
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


def _class_badge(paper_class: PaperClass) -> str:
    return f'<span class="tag tag-{paper_class.value.lower()}">{paper_class.value}</span>'


def _render_header(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="app-header"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def _artifact_claims(stats: dict) -> tuple[tuple[str, str, str], ...]:
    """Build the headline cards from live corpus counts, so they cannot drift."""
    total = stats["total_papers"]
    with_abstracts = stats["with_abstracts"]
    with_bibtex = stats.get("with_bibtex", 0)
    venues = len(stats.get("by_event", ()))
    return (
        ("Corpus", f"{total:,}", f"cybersecurity papers across {venues} venues"),
        (
            "Abstracts",
            f"{with_abstracts / total:.1%}" if total else "n/a",
            f"{with_abstracts:,} searchable abstracts",
        ),
        (
            "BibTeX",
            f"{with_bibtex / total:.1%}" if total else "n/a",
            "records ready for citation export",
        ),
        ("Verification", "Offline", "integrity checks for the selected snapshot"),
    )


def _render_claims(stats: dict) -> None:
    # The HTML must stay flat: Streamlit runs markdown before inserting raw
    # HTML, so any line indented four or more spaces becomes a code block.
    cards = "".join(
        '<div class="claim">'
        f'<div class="name">{_safe_html(name)}</div>'
        f'<div class="value">{_safe_html(value)}</div>'
        f'<div class="note">{_safe_html(note)}</div>'
        "</div>"
        for name, value, note in _artifact_claims(stats)
    )
    st.markdown(f'<div class="claim-grid">{cards}</div>', unsafe_allow_html=True)


def _render_metrics(stats: dict, filtered_count: int | None = None) -> None:
    total = stats["total_papers"]
    with_abs = stats["with_abstracts"]
    with_bib = stats.get("with_bibtex", 0)
    abs_pct = (with_abs / total * 100) if total else 0
    bib_pct = (with_bib / total * 100) if total else 0
    venues = len(stats["by_event"])
    extra = (
        f'<div class="metric green"><div class="lbl">Currently shown</div>'
        f'<div class="val">{filtered_count:,}</div></div>'
        if filtered_count is not None else ""
    )
    st.markdown(
        '<div class="metric-row">'
        f'<div class="metric"><div class="lbl">Papers indexed</div>'
        f'<div class="val">{total:,}</div>'
        f'<div class="sub">across {venues} venues</div></div>'
        f'<div class="metric amber"><div class="lbl">With abstract</div>'
        f'<div class="val">{with_abs:,}</div>'
        f'<div class="sub">{abs_pct:.2f}% coverage</div></div>'
        f'<div class="metric rose"><div class="lbl">With BibTeX</div>'
        f'<div class="val">{with_bib:,}</div>'
        f'<div class="sub">{bib_pct:.2f}% coverage</div></div>'
        f'{extra}'
        '</div>',
        unsafe_allow_html=True,
    )


def _reset_search_state() -> None:
    """Restore every search widget to a coherent default state."""
    defaults = {
        "search_ranked": "",
        "search_title": "",
        "search_abstract": "",
        "search_author": "",
        "search_author_position": "Any position",
        "search_topic": "",
        "search_area": "All areas",
        "search_tier_scope": "All declared venues",
        "search_venue": "All venues",
        "search_year": "All years",
        "search_class": [],
        "search_abstract_scope": "Any",
        "search_bibtex": False,
        "search_awards": False,
    }
    for key, value in defaults.items():
        st.session_state[key] = value
    st.session_state.pop("search_signature", None)
    st.session_state["page_no"] = 1


def _open_search_from_insight(
    venue: str | None = None,
    year: int | None = None,
    topic: str | None = None,
    author: str | None = None,
    author_position: str | None = None,
    area: str | None = None,
    paper_class: str | None = None,
    tier_scope: str | None = None,
) -> None:
    """Transfer one insight dimension into the search workflow."""
    _reset_search_state()
    st.session_state["search_venue"] = venue or "All venues"
    st.session_state["search_year"] = year or "All years"
    st.session_state["search_topic"] = topic or ""
    st.session_state["search_author"] = author or ""
    st.session_state["search_author_position"] = author_position or "Any position"
    st.session_state["search_area"] = area or "All areas"
    st.session_state["search_class"] = [paper_class] if paper_class else []
    st.session_state["search_tier_scope"] = tier_scope or "All declared venues"
    st.session_state["page"] = "Search"


def _queue_search_from_chart(**filters: str | int | None) -> None:
    """Navigate after a chart event without mutating an instantiated widget."""
    st.session_state["pending_search_navigation"] = filters
    st.rerun()


def _interactive_bar_chart(
    data: pd.DataFrame,
    category: str,
    value: str,
    key: str,
    height: int,
    *,
    horizontal: bool = True,
    sort: str | list | None = "-x",
    color: str = "#2f6f73",
) -> object | None:
    """Render a restrained selectable chart and return its selected category."""
    selection_name = f"{key}_selection"
    selection = alt.selection_point(selection_name, fields=[category], on="click", clear="dblclick")
    category_encoding = alt.Y(f"{category}:N", sort=sort, title=None)
    value_encoding = alt.X(f"{value}:Q", title=value)
    if not horizontal:
        category_encoding = alt.X(
            f"{category}:O", sort=sort, title=category, axis=alt.Axis(labelAngle=0)
        )
        value_encoding = alt.Y(f"{value}:Q", title=value)
    chart = (
        alt.Chart(data)
        .mark_bar(color=color, cornerRadiusEnd=3)
        .encode(
            x=value_encoding if horizontal else category_encoding,
            y=category_encoding if horizontal else value_encoding,
            tooltip=[alt.Tooltip(f"{category}:N"), alt.Tooltip(f"{value}:Q", format=",")],
            opacity=alt.condition(selection, alt.value(1.0), alt.value(0.58)),
        )
        .add_params(selection)
        .properties(height=height)
        .configure_axis(
            domainColor="#cbd5e1",
            gridColor="#e7ebee",
            labelColor="#475569",
            titleColor="#334155",
            labelFontSize=12,
            titleFontSize=12,
        )
        .configure_view(strokeOpacity=0)
    )
    event = st.altair_chart(chart, key=key, on_select="rerun", selection_mode=selection_name, theme=None)
    return selected_chart_value(event, selection_name, category)


def _interactive_line_chart(
    data: pd.DataFrame, x_field: str, y_field: str, key: str, height: int
) -> object | None:
    """Render a chronological selectable line chart with precise values."""
    selection_name = f"{key}_selection"
    selection = alt.selection_point(selection_name, fields=[x_field], on="click", clear="dblclick")
    line = alt.Chart(data).mark_line(color="#334e68", strokeWidth=2.5)
    points = alt.Chart(data).mark_point(filled=True, color="#334e68", size=75)
    chart = (
        (line + points)
        .encode(
            x=alt.X(f"{x_field}:O", sort="ascending", title=x_field, axis=alt.Axis(labelAngle=0)),
            y=alt.Y(f"{y_field}:Q", title=y_field, scale=alt.Scale(zero=True)),
            tooltip=[alt.Tooltip(f"{x_field}:O"), alt.Tooltip(f"{y_field}:Q", format=".2f")],
            opacity=alt.condition(selection, alt.value(1.0), alt.value(0.62)),
        )
        .add_params(selection)
        .properties(height=height)
        .configure_axis(
            domainColor="#cbd5e1",
            gridColor="#e7ebee",
            labelColor="#475569",
            titleColor="#334155",
            labelFontSize=12,
            titleFontSize=12,
        )
        .configure_view(strokeOpacity=0)
    )
    event = st.altair_chart(chart, key=key, on_select="rerun", selection_mode=selection_name, theme=None)
    return selected_chart_value(event, selection_name, x_field)


# ── Pages ──────────────────────────────────────────────────────────────────


def page_artifact() -> None:
    _render_header(
        "Reproducible corpus overview",
        "Reproduce the corpus, inspect coverage, and export ready-to-cite references from a local snapshot.",
    )
    _render_claims(_load_collector().db.get_statistics())

    st.subheader("Start from a research question")
    tier1_col, broad_col, monitor_col = st.columns(3)
    with tier1_col:
        st.markdown("**Reference mapping**  ")
        st.caption(
            "Use Security Big Four (Tier 1) to identify canonical venue papers and recurring authors."
        )
    with broad_col:
        st.markdown("**Review protocol**  ")
        st.caption(
            "Start with the declared full scope, then record any venue restriction as an inclusion decision."
        )
    with monitor_col:
        st.markdown("**Research monitoring**  ")
        st.caption(
            "Use topic, year, tier, and author-position filters to decide which new work to inspect."
        )

    st.subheader("Verification path")
    st.markdown(
        """
        1. Run the reproduction script to validate the headline claims.
        2. Use Search to inspect the corpus and export CSV, JSON or BibTeX.
        3. Use Insights to verify scope, coverage and temporal distribution.
        4. Use Dataset lifecycle only when creating a new successor from live sources.
        """
    )

    st.code("bash reproduce.sh", language="bash")

    st.subheader("Reproducibility evidence")
    evidence = pd.DataFrame(
        [
            {
                "Criterion": "Availability",
                "Evidence": "Source code, compressed SQLite snapshot, manifest, and reviewer documentation.",
            },
            {
                "Criterion": "Functionality",
                "Evidence": "CLI, Streamlit interface, search, statistics and CSV/JSON/BibTeX export.",
            },
            {
                "Criterion": "Reproducibility",
                "Evidence": "One command validates the manifest, materializes the snapshot, runs tests, exercises search, and exports BibTeX.",
            },
            {
                "Criterion": "Sustainability",
                "Evidence": "Small Python/SQLite stack, typed models and configuration-driven corpus scope.",
            },
        ]
    )
    st.dataframe(evidence, width="stretch", hide_index=True)

    st.subheader("Release evidence")
    findings = pd.DataFrame(
        [
            {
                "Check": "Snapshot identity",
                "Result": "The manifest records counts and SHA-256 for the compressed SQLite release.",
                "Use": "bash reproduce.sh",
            },
            {
                "Check": "Search and export",
                "Result": "FTS5 ranking, filters, and CSV/JSON/BibTeX exports run against the verified local copy.",
                "Use": "Search page or python -m src.cli",
            },
        ]
    )
    st.dataframe(findings, width="stretch", hide_index=True)


def page_search() -> None:
    collector = _load_collector()
    stats = collector.db.get_statistics()

    with st.sidebar:
        st.markdown("## Filters")

        with st.expander("Text", expanded=True):
            rank_query = st.text_input(
                "Ranked search (BM25)",
                placeholder="e.g., memory corruption mitigations",
                help="Relevance-ranked full-text search over title, abstract and "
                     "authors. Overrides the substring filters below.",
                key="search_ranked",
            )
            title_query = st.text_input(
                "Title contains", placeholder="e.g., authentication", key="search_title"
            )
            abstract_query = st.text_input(
                "Abstract contains", placeholder="e.g., LLM, SGX", key="search_abstract"
            )
            author_query = st.text_input(
                "Author contains", placeholder="e.g., Sekar", key="search_author"
            )
            author_position = st.selectbox(
                "Author position",
                ["Any position", "First author", "Last author"],
                key="search_author_position",
                help="Applied only when Author contains is set.",
            )
            tech_query = st.text_input(
                "Topic / tech", placeholder="e.g., blockchain, 5G", key="search_topic"
            )

        with st.expander("Venue & year", expanded=True):
            area_choice = st.selectbox(
                "Research area",
                ["All areas", "security", "ai", "networks", "mobile", "systems", "cross-area"],
                key="search_area",
            )
            tier_scope = st.selectbox(
                "Venue tier scope",
                tier_scope_options(),
                help="Security Big Four (Tier 1): ACM CCS, IEEE S&P, USENIX Security, and NDSS.",
                key="search_tier_scope",
            )
            allowed_tiers = tiers_in_scope(tier_scope)
            venue_options = _venue_options(collector, allowed_tiers)
            if st.session_state.get("search_venue") not in venue_options:
                st.session_state["search_venue"] = "All venues"
            venue_choice = st.selectbox("Venue", venue_options, key="search_venue")
            year_choice = st.selectbox(
                "Year", ["All years", *sorted(stats["by_year"], reverse=True)], key="search_year"
            )

        with st.expander("Paper class", expanded=False):
            class_choices = st.multiselect(
                "Include", [c.value for c in PaperClass],
                help="Filter by SoK, Survey, Poster, Workshop, Short, Journal or Article.",
                key="search_class",
            )

        with st.expander("Abstract & citation", expanded=False):
            abstract_length = st.selectbox(
                "Abstract availability / length",
                ["Any", "Has abstract", "Missing abstract", "Short (≤ 150 words)",
                 "Medium (151–300 words)", "Long (> 300 words)"],
                key="search_abstract_scope",
            )
            only_with_bibtex = st.checkbox(
                "Has BibTeX", help="Only include papers whose BibTeX entry has been fetched.",
                key="search_bibtex",
            )

        with st.expander("Awards", expanded=False):
            awards_only = st.checkbox(
                "Award winners only",
                help="Only papers with a recorded Best or Distinguished Paper award.",
                key="search_awards",
            )

        st.button("Reset all filters", on_click=_reset_search_state, width="stretch")

        st.markdown("## Display")
        page_size = st.select_slider(
            "Results per page", options=PAGE_SIZE_OPTIONS, value=50, key="search_page_size"
        )
        sort_choice = st.selectbox(
            "Sort by",
            ["Relevance", "Year (newest first)", "Year (oldest first)",
             "Title (A–Z)", "Venue"],
            help="Relevance follows the ranked-search order and falls back to "
                 "newest-first when no ranked query is set.",
            key="search_sort",
        )

    filters = SearchFilters()
    if title_query:
        filters.title_contains = title_query
    if abstract_query:
        filters.abstract_contains = abstract_query
    if author_query:
        filters.author_contains = author_query
    if tech_query:
        filters.technology = tech_query
    if venue_choice != "All venues":
        filters.event = venue_choice
    if year_choice != "All years":
        filters.year = int(year_choice)
    allowed_tiers = tiers_in_scope(tier_scope)

    award_map = _award_map()
    if rank_query:
        # Relevance mode: BM25 over the FTS index, best match first. Venue and
        # year go into the SQL; the remaining filters apply below as usual.
        from src.models import Paper

        ranked_rows = collector.db.search_ranked(
            rank_query,
            event=filters.event,
            year=filters.year,
            limit=None,
        )
        results = [
            Paper(**{
                field: row[field]
                for field in Paper.model_fields
                if field in row and row[field] is not None
            })
            for row in ranked_rows
        ]
    else:
        results = collector.search(filters, limit=None)
    if allowed_tiers is not None:
        results = [paper for paper in results if tier_for(paper.event) in allowed_tiers]
    if area_choice != "All areas":
        results = [paper for paper in results if area_for(paper.event) == area_choice]
    if author_query and author_position != "Any position":
        position_key = {"First author": "first", "Last author": "last"}[author_position]
        normalized_query = author_query.casefold()
        results = [
            paper
            for paper in results
            if any(
                normalized_query in author.casefold()
                for author in authors_at_position(paper.authors, position_key)
            )
        ]
    if class_choices:
        wanted = {PaperClass(value) for value in class_choices}
        results = [p for p in results if p.paper_class in wanted]
    results = _abstract_length_predicate(results, abstract_length)
    results = _bibtex_predicate(results, only_with_bibtex)
    if awards_only:
        results = [paper for paper in results if paper.paper_id in award_map]

    if rank_query and sort_choice == "Relevance":
        pass  # search_ranked already returns best-first order
    elif sort_choice == "Year (newest first)":
        results.sort(key=lambda p: (-(p.year or 0), p.title or ""))
    elif sort_choice == "Year (oldest first)":
        results.sort(key=lambda p: (p.year or 0, p.title or ""))
    elif sort_choice == "Title (A–Z)":
        results.sort(key=lambda p: (p.title or "").lower())
    elif sort_choice == "Venue":
        results.sort(key=lambda p: (p.event or "", -(p.year or 0)))

    _render_header(
        "Security Paper Explorer",
        "Search a curated dataset from the configured security literature scope.",
    )
    _render_metrics(stats, filtered_count=len(results))
    active_venue = venue_choice if venue_choice != "All venues" else tier_scope
    st.caption(
        f"Active venue scope: {active_venue}. Snapshot: {collector.config.profile_id}."
    )

    if not results:
        st.info("No papers match the current filters. Try widening the search.")
        return

    total_pages = max(1, (len(results) + page_size - 1) // page_size)
    search_signature = (
        rank_query,
        title_query,
        abstract_query,
        author_query,
        author_position,
        tech_query,
        area_choice,
        venue_choice,
        year_choice,
        tier_scope,
        tuple(class_choices),
        abstract_length,
        only_with_bibtex,
        awards_only,
        page_size,
        sort_choice,
    )
    if st.session_state.get("search_signature") != search_signature:
        st.session_state["page_no"] = 1
        st.session_state["search_signature"] = search_signature
    st.session_state["page_no"] = min(
        max(1, int(st.session_state.get("page_no", 1))),
        total_pages,
    )

    col_count, col_page = st.columns([3, 1])
    with col_page:
        if total_pages > 1:
            nav_prev, nav_next = st.columns(2)
            with nav_prev:
                if st.button("‹", disabled=st.session_state["page_no"] <= 1, width="stretch"):
                    st.session_state["page_no"] -= 1
                    st.rerun()
            with nav_next:
                if st.button("›", disabled=st.session_state["page_no"] >= total_pages, width="stretch"):
                    st.session_state["page_no"] += 1
                    st.rerun()
            page = int(st.number_input("Page", 1, total_pages, key="page_no"))
        else:
            page = 1

    start = (page - 1) * page_size
    end = min(len(results), start + page_size)
    page_slice = results[start : start + page_size]
    with col_count:
        st.markdown(
            f'<div class="results-bar">'
            f'<span class="count">{len(results):,} papers found</span>'
            f'<span class="sub">showing {start + 1:,}–{end:,} · '
            f'page {page} of {total_pages} · {page_size} per page</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    table_rows = [
        {
            "Title": paper.title or "—",
            "Authors": (paper.authors or "—")[:90]
                       + ("…" if paper.authors and len(paper.authors) > 90 else ""),
            "Venue": paper.event or "—",
            "Tier": tier_for(paper.event),
            "Year": paper.year,
            "Award": _award_label(award_map.get(paper.paper_id)),
            "Class": paper.paper_class.value,
            "Words": paper.abstract_words,
            "Abstract": _truncate(paper.abstract),
            "Cite": paper.cite_command or "—",
            "Link": paper.ee or paper.url or "",
        }
        for paper in page_slice
    ]
    df = pd.DataFrame(table_rows)

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        height=min(700, 70 + len(df) * 56),
        column_config={
            "Title":    st.column_config.TextColumn("Title", width="medium"),
            "Authors":  st.column_config.TextColumn("Authors", width="small"),
            "Venue":    st.column_config.TextColumn("Venue", width="small"),
            "Tier":     st.column_config.TextColumn("Tier", width="small"),
            "Year":     st.column_config.NumberColumn("Year", format="%d", width="small"),
            "Award":    st.column_config.TextColumn("Award", width="small"),
            "Class":    st.column_config.TextColumn("Class", width="small"),
            "Words":    st.column_config.NumberColumn("Words", format="%d", width="small"),
            "Abstract": st.column_config.TextColumn("Abstract preview", width="large"),
            "Cite":     st.column_config.TextColumn("\\cite{…}", width="small"),
            "Link":     st.column_config.LinkColumn("DOI / URL", width="small", display_text="open"),
        },
    )

    full_rows = [
        {
            "title": paper.title,
            "authors": paper.authors,
            "first_author": paper.first_author,
            "venue": paper.event,
            "tier": tier_for(paper.event),
            "year": paper.year,
            "class": paper.paper_class.value,
            "abstract_words": paper.abstract_words,
            "doi": paper.doi,
            "ee": paper.ee,
            "url": paper.url,
            "abstract": paper.abstract,
            "cite_key": paper.cite_key,
            "bibtex": paper.bibtex,
        }
        for paper in results
    ]
    full_df = pd.DataFrame(full_rows)
    bib_text = "\n\n".join(paper.bibtex for paper in results if paper.bibtex)
    col_csv, col_json, col_bib, _ = st.columns([1, 1, 1, 3])
    with col_csv:
        st.download_button(
            "Export CSV",
            full_df.to_csv(index=False).encode("utf-8"),
            "topvenues_results.csv",
            "text/csv",
            width="stretch",
        )
    with col_json:
        st.download_button(
            "Export JSON",
            full_df.to_json(orient="records", indent=2),
            "topvenues_results.json",
            "application/json",
            width="stretch",
        )
    with col_bib:
        st.download_button(
            "Export BibTeX",
            bib_text or "% no BibTeX entries available",
            "topvenues_results.bib",
            "application/x-bibtex",
            width="stretch",
            disabled=not bib_text,
            help="LaTeX bibliography file with one BibTeX entry per result."
                 if bib_text else "BibTeX not yet fetched for any paper in this result set.",
        )

    st.divider()
    st.subheader("Paper details")
    title_options = [f"[{paper.year}] {paper.title}" for paper in page_slice]
    selected_label = st.selectbox(
        "Select a paper from this page", title_options, label_visibility="collapsed"
    )
    if selected_label:
        idx = title_options.index(selected_label)
        paper = page_slice[idx]
        link = paper.ee or paper.url
        link_html = (
            f'<a href="{_safe_html(link)}" target="_blank">{_safe_html(link)}</a>'
            if link else "—"
        )
        doi_html = (
            f'<a href="https://doi.org/{_safe_html(paper.doi)}" target="_blank">{_safe_html(paper.doi)}</a>'
            if paper.doi else "—"
        )
        abstract_html = (
            _safe_html(paper.abstract) if paper.abstract
            else "<i>No abstract available.</i>"
        )
        st.markdown(
            '<div class="paper-card">'
            f'<h3>{_safe_html(paper.title)}</h3>'
            '<div class="paper-meta">'
            f'<span><b>Authors:</b> {_safe_html(paper.authors)}</span>'
            f'<span><b>Venue:</b> {_safe_html(paper.event)}</span>'
            f'<span><b>Tier:</b> {_safe_html(tier_for(paper.event))}</span>'
            f'<span><b>Year:</b> {_safe_html(paper.year)}</span>'
            f'<span><b>Words:</b> {paper.abstract_words:,}</span>'
            f'<span><b>DOI:</b> {doi_html}</span>'
            f'<span><b>Link:</b> {link_html}</span>'
            '</div>'
            f'<div>{_class_badge(paper.paper_class)}</div>'
            '<hr style="border:none; border-top:1px solid var(--border); margin:1rem 0">'
            f'<div class="paper-abstract">{abstract_html}</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        if paper.bibtex:
            st.markdown("**BibTeX**")
            st.code(paper.bibtex, language="bibtex")
            col_cite, _ = st.columns([1, 3])
            with col_cite:
                st.code(paper.cite_command or "", language="latex")
        else:
            st.caption("BibTeX not yet fetched. Run `python -m src.cli bibtex` to populate.")


def page_insights() -> None:
    collector = _load_collector()
    stats = collector.db.get_statistics()
    _render_header(
        "Dataset insights",
        "Distribution of papers across venues, years, paper classes and abstract coverage.",
    )
    _render_metrics(stats)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Papers by venue")
        venue_df = pd.DataFrame(
            [{"Venue": k, "Papers": v} for k, v in
             sorted(stats["by_event"].items(), key=lambda x: x[1], reverse=True)]
        )
        selected_venue = _interactive_bar_chart(venue_df, "Venue", "Papers", "venue_chart", 460)
        st.caption("Click a bar to open that venue's records. Double-click clears the selection.")
        if selected_venue:
            _queue_search_from_chart(venue=str(selected_venue))

    with col2:
        st.subheader("Papers by year")
        year_df = pd.DataFrame(
            [{"Year": k, "Papers": v} for k, v in sorted(stats["by_year"].items())]
        )
        selected_year = _interactive_bar_chart(
            year_df,
            "Year",
            "Papers",
            "year_chart",
            460,
            horizontal=False,
            sort="ascending",
            color="#334e68",
        )
        st.caption("Click a bar to open that year's records. Double-click clears the selection.")
        partial_years = sorted(set(collector.config.partial_years) & set(stats["by_year"]))
        if partial_years:
            partial_year_labels = ", ".join(str(year) for year in partial_years)
            st.caption(
                f"Partial publication year(s) in this frozen release: {partial_year_labels}. "
                "Compare completed years before inferring annual growth."
            )
        if selected_year is not None:
            _queue_search_from_chart(year=int(selected_year))

    st.divider()
    st.subheader("Papers by class")
    class_counts = {}
    for paper in collector.papers:
        class_counts[paper.paper_class.value] = class_counts.get(paper.paper_class.value, 0) + 1
    class_df = pd.DataFrame(
        [{"Class": k, "Papers": v} for k, v in
         sorted(class_counts.items(), key=lambda x: x[1], reverse=True)]
    )
    selected_class = _interactive_bar_chart(
        class_df, "Class", "Papers", "class_chart", 320, color="#a35f25"
    )
    st.caption("Click a bar to open records in that paper class.")
    if selected_class:
        _queue_search_from_chart(paper_class=str(selected_class))

    st.divider()
    st.subheader("Topic trend")
    st.caption(
        "Yearly volume and corpus share for a topic (title/abstract match), "
        "with the venues that publish it most. Share normalizes by each "
        "year's corpus size, so corpus growth does not masquerade as topic "
        "growth. Counts are a lower bound outside the abstract-enriched "
        "layers."
    )
    col_trend_topic, col_trend_area, col_trend_tier = st.columns([2, 1, 1.4])
    with col_trend_topic:
        trend_topic = st.text_input(
            "Topic", placeholder="e.g., LLM, ransomware, fuzzing",
            key="trend_topic",
        )
    with col_trend_area:
        trend_area = st.selectbox(
            "Area", ["All areas", "security", "ai", "networks", "mobile",
                     "systems", "cross-area"],
            key="trend_area",
        )
    with col_trend_tier:
        trend_tier_scope = st.selectbox(
            "Venue tier scope",
            tier_scope_options(),
            key="trend_tier_scope",
        )
    if trend_topic:
        trend = _cached_topic_trend(
            str(collector.db.db_path), trend_topic,
            None if trend_area == "All areas" else trend_area,
            trend_tier_scope,
        )
        if trend["total"]:
            trend_df = pd.DataFrame(trend["by_year"]).set_index("year")
            col_abs, col_share = st.columns(2)
            with col_abs:
                st.caption(f"Papers per year — {trend['total']:,} total")
                selected_trend_year = _interactive_bar_chart(
                    trend_df.reset_index().rename(columns={"year": "Year", "papers": "Papers"}),
                    "Year",
                    "Papers",
                    "trend_chart",
                    280,
                    horizontal=False,
                    sort="ascending",
                    color="#2f6f73",
                )
            with col_share:
                st.caption("Share of the year's corpus (%)")
                selected_share_year = _interactive_line_chart(
                    trend_df.reset_index().rename(
                        columns={"year": "Year", "share_pct": "Share (%)"}
                    ),
                    "Year",
                    "Share (%)",
                    "trend_share_chart",
                    280,
                )
            venues = " · ".join(
                f"{event} ({count:,})" for event, count in trend["top_venues"]
            )
            st.markdown(f"**Main venues:** {venues}")
            partial_trend_years = sorted(
                set(collector.config.partial_years)
                & {row["year"] for row in trend["by_year"]}
            )
            if partial_trend_years:
                partial_year_labels = ", ".join(str(year) for year in partial_trend_years)
                st.caption(
                    f"Interpret {partial_year_labels} as partial-year observations, not as "
                    "completed annual trends."
                )
            selected_topic_year = (
                selected_trend_year
                if selected_trend_year is not None
                else selected_share_year
            )
            if selected_topic_year is not None:
                _queue_search_from_chart(
                    year=int(selected_topic_year),
                    topic=trend_topic,
                    tier_scope=trend_tier_scope,
                )
        else:
            st.info("No papers match this topic in the selected scope.")

    st.divider()
    st.subheader("Researcher Radar")
    st.caption(
        "Discover researchers who recur in the selected corpus. Paper count is the "
        "transparent default; the optional tier-weighted view gives Big Four papers "
        "more weight. Neither view measures citations, quality, seniority, or authority. "
        "DBLP identity suffixes are preserved to avoid merging homonyms."
    )
    st.caption(
        "Choose all, first, or last authorship position to answer different "
        "literature-review questions; none is a proxy for citation impact or seniority."
    )
    col_topic, col_area, col_tier, col_position, col_metric, col_n = st.columns(
        [2, 1, 1.35, 1, 1.25, 0.75]
    )
    with col_topic:
        author_topic = st.text_input(
            "Topic (title/abstract contains)", placeholder="e.g., LLM, fuzzing",
            key="authors_topic",
        )
    with col_area:
        author_area = st.selectbox(
            "Area", ["All areas", "security", "ai", "networks", "mobile",
                     "systems", "cross-area"],
            key="authors_area",
        )
    with col_tier:
        author_tier_scope = st.selectbox(
            "Venue tier scope",
            tier_scope_options(),
            key="authors_tier_scope",
            help="Use Security Big Four (Tier 1) to identify recurring authors in CCS, S&P, USENIX Security, and NDSS only.",
        )
    with col_position:
        author_position = st.selectbox(
            "Authorship", ["Any author", "First author", "Last author"],
            key="authors_position",
            help="Rank all appearances, first-author appearances, or last-author appearances.",
        )
    with col_metric:
        author_metric = st.selectbox(
            "Ranking metric",
            ["Paper count", "Tier-weighted visibility"],
            key="authors_metric",
            help="Paper count answers the requested frequency ranking. The weighted view is a separate, declared heuristic.",
        )
    with col_n:
        author_limit = st.number_input("Authors", 5, 50, 15, key="authors_limit")

    ranked_authors = _cached_reference_authors(
        str(collector.db.db_path),
        author_topic or None,
        None if author_area == "All areas" else author_area,
        {"Any author": "any", "First author": "first", "Last author": "last"}[author_position],
        author_tier_scope,
        {"Paper count": "paper_count", "Tier-weighted visibility": "tier_weighted"}[
            author_metric
        ],
        int(author_limit),
    )
    if ranked_authors:
        author_table = pd.DataFrame([
            {
                "#": position,
                "Author": entry["author"],
                "Tier-weighted score": entry["score"],
                "Papers": entry["papers"],
                "Top-4": entry["top4"],
                "Other top-tier": entry["top_tier"],
                "Top-4 regional": entry["top4_regional"],
                "Awards": entry["awards"],
                f"Recent ({entry['recent_since']}–{entry['recent_through']})": entry[
                    "recent_papers"
                ],
                "Active": f"{entry['first_year']}–{entry['last_year']}",
                "Main venues": ", ".join(entry["venues"]),
                "Tier scope": author_tier_scope,
                "Topic": author_topic or "",
                "Area": "" if author_area == "All areas" else author_area,
                "Authorship": author_position,
                "Ranking metric": author_metric,
            }
            for position, entry in enumerate(ranked_authors, start=1)
        ])
        st.caption(
            f"Active scope: {author_tier_scope} · {author_position.lower()} · "
            f"{author_area} · {author_metric.lower()} · topic: {author_topic or 'any'}"
        )
        st.dataframe(
            author_table.drop(
                columns=["Tier scope", "Topic", "Area", "Authorship", "Ranking metric"]
            ),
            width="stretch",
            hide_index=True,
        )
        selected_author = st.selectbox(
            "Inspect an author's corpus records", [entry["author"] for entry in ranked_authors]
        )
        open_col, export_col = st.columns([1, 1])
        with open_col:
            st.button(
                "Open author records",
                key="open_author_records",
                on_click=_open_search_from_insight,
                kwargs={
                    "author": selected_author,
                    "author_position": author_position,
                    "topic": author_topic or None,
                    "area": None if author_area == "All areas" else author_area,
                    "tier_scope": author_tier_scope,
                },
                width="stretch",
            )
        with export_col:
            st.download_button(
                "Download author shortlist (CSV)",
                author_table.to_csv(index=False).encode("utf-8"),
                file_name="topvenues-author-shortlist.csv",
                mime="text/csv",
                width="stretch",
            )
    else:
        st.info("No authors match the current topic/area scope.")

    st.divider()
    st.subheader("Abstract coverage by venue")
    rows = []
    with sqlite3.connect(collector.db.db_path) as conn:
        for venue, total in stats["by_event"].items():
            with_abs = conn.execute(
                "SELECT COUNT(*) FROM papers "
                "WHERE event=? AND abstract IS NOT NULL AND abstract!=''",
                (venue,),
            ).fetchone()[0]
            rows.append({
                "Venue": venue,
                "Total": total,
                "With abstract": with_abs,
                "Coverage": f"{with_abs / total * 100:.1f}%" if total else "—",
            })
    coverage_df = pd.DataFrame(rows)
    coverage_df["Coverage (%)"] = coverage_df["Coverage"].str.rstrip("%").astype(float)
    selected_coverage_venue = _interactive_bar_chart(
        coverage_df,
        "Venue",
        "Coverage (%)",
        "coverage_chart",
        460,
        color="#537a4a",
    )
    st.caption("Click a coverage bar to inspect the venue's records and missing abstracts.")
    if selected_coverage_venue:
        _queue_search_from_chart(venue=str(selected_coverage_venue))
    st.dataframe(coverage_df.drop(columns="Coverage (%)"), width="stretch", hide_index=True)


def page_evidence() -> None:
    """Keep released-profile claims separate from companion-study evidence."""
    _render_header(
        "Evidence and claim boundaries",
        "What this snapshot verifies, and what requires a separate empirical protocol.",
    )
    st.subheader("Current release: security-20-v3")
    st.markdown(
        "This interface verifies the manifest, exact-resource identity policy, coverage, search, "
        "exports, and platform reproduction for the selected snapshot. It does not claim a manual "
        "accuracy audit or cross-index comparison for this successor profile."
    )
    st.subheader("Companion full-paper evaluation")
    st.markdown(
        "The published full-paper protocol is bound to a different frozen 9,925-record snapshot "
        "(SHA-256 `0f4dbaa9…ef64cd`): a venue-stratified 200-record live comparison and a 200-record "
        "manual publisher-source audit. Its data, instrument, labels, and offline summarizer are "
        "available in the [frozen evaluation package](https://github.com/sidneibarbieri/topVenues/tree/07674480ff3172f4b195387438ab3af3c9c5655f/evaluation/baseline_validation)."
    )
    st.info(
        "Those results are evidence for the companion snapshot only. Reusing them as v3 accuracy "
        "would be invalid; a v3 audit needs a new sampled-label protocol."
    )
    st.subheader("Identity policy")
    st.markdown(
        "v3 inherits exact-resource deduplication, enforces the declared 2019–2026 window, and "
        "merges two additional DOI aliases confirmed by Crossref. Four same-metadata pairs remain "
        "distinct because publisher resources remain distinct. Every decision is disclosed in "
        "data/adjudication/security-20-v3-identity.json."
    )


def page_pipeline() -> None:
    collector = _load_collector()
    _render_header(
        "Pipeline",
        "Run the data collection pipeline. Each step is incremental and safe to repeat.",
    )

    if collector.config.immutable_snapshot:
        st.warning(
            "This is a released immutable profile. Interactive refresh controls are disabled so "
            "a live API run cannot alter the corpus shown in this release. Create, validate, and "
            "publish a separate successor profile for any refresh."
        )
        st.markdown(
            "Refreshes are created as a new named profile through the "
            "[profile refresh procedure](https://github.com/sidneibarbieri/"
            "topvenues-tool/blob/main/docs/PROFILE_REFRESH.md). The current snapshot is never "
            "modified in place."
        )
        return

    tab_dl, tab_cons, tab_extr = st.tabs(["Download", "Consolidate", "Extract abstracts"])

    with tab_dl:
        st.write("Fetches DBLP JSON files for every configured venue and year. "
                 "Skips files that already exist and validate cleanly.")
        if st.button("Run download", type="primary", width="stretch", key="dl_btn"):
            with st.spinner("Downloading…"):
                _run_async(Collector().run_download())
                st.success("Download complete.")
                st.cache_resource.clear()

    with tab_cons:
        st.write("Merges downloaded JSON into the SQLite database. Existing abstracts "
                 "are preserved (idempotent upsert with `COALESCE`).")
        if st.button("Run consolidate", type="primary", width="stretch", key="cons_btn"):
            with st.spinner("Consolidating…"):
                _run_async(Collector().run_consolidate())
                st.success("Consolidation complete.")
                st.cache_resource.clear()

    with tab_extr:
        st.warning(
            "Rate-limited. Open APIs (Semantic Scholar / OpenAlex / CrossRef) run in "
            "parallel; publisher scrapers run sequentially with throttling."
        )
        col_a, col_b = st.columns(2)
        with col_a:
            batch_size = st.number_input("Batch size", 1, 100, 10)
        with col_b:
            max_papers = st.number_input("Max papers (0 = all)", 0, 10000, 0)

        if st.button("Run extraction", type="primary", width="stretch", key="ext_btn"):
            collector = Collector()
            collector.config.batch_size = batch_size
            collector.papers = collector._load_papers_from_disk()
            to_process = [p for p in collector.papers if not p.abstract]
            if max_papers > 0:
                to_process = to_process[:max_papers]
            if not to_process:
                st.info("All papers already have abstracts.")
                return
            progress = st.progress(0.0)
            status = st.empty()
            total = len(to_process)
            status.text(f"0 / {total} papers processed…")

            async def run_extraction():
                fetcher = AbstractFetcher(collector)
                for idx, paper in enumerate(to_process, 1):
                    await collector._extract_single_abstract(paper, fetcher)
                    progress.progress(idx / total)
                    status.text(f"{idx} / {total} papers processed…")
                    if idx % collector.config.batch_size == 0:
                        collector._save_dataset()
                        await asyncio.sleep(60)
                await fetcher.close()
                collector._save_dataset()

            _run_async(run_extraction())
            st.success("Extraction complete.")
            st.cache_resource.clear()


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> None:
    pending = st.session_state.pop("pending_search_navigation", None)
    if pending:
        _open_search_from_insight(**pending)
    pages = {
        "Overview": page_artifact,
        "Search": page_search,
        "Insights": page_insights,
        "Evidence": page_evidence,
        "Dataset lifecycle": page_pipeline,
    }
    with st.sidebar:
        st.markdown(
            '<h2 style="color:#fff !important; border:none !important;'
            'font-size:1.15rem !important; text-transform:none !important;'
            'letter-spacing:0 !important; margin-bottom:1rem !important">'
            'TopVenues</h2>',
            unsafe_allow_html=True,
        )
        page = st.radio("Navigate", list(pages.keys()), label_visibility="collapsed", key="page")
        st.markdown("<br>", unsafe_allow_html=True)

    pages[page]()

    st.markdown(
        '<div class="footer">TopVenues — bibliographic explorer · '
        'data sourced from DBLP, Semantic Scholar, OpenAlex, CrossRef</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
