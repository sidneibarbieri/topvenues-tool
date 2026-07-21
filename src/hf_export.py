"""Export the corpus as a Hugging Face dataset (Parquet + dataset card).

The export is derived from the released SQLite snapshot, so publishing to the
Hub is reproducible: the same snapshot always produces the same Parquet file
and the same dataset card statistics.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .areas import area_for

# Columns published on the Hub, in viewer display order. Bookkeeping columns
# (created_at/updated_at) and sparse internal fields (score/access) stay local.
_EXPORT_COLUMNS = [
    "paper_id",
    "key",
    "title",
    "authors",
    "event",
    "venue",
    "area",
    "year",
    "paper_type",
    "pages",
    "url",
    "ee",
    "abstract",
    "bibtex",
]

_CARD_TEMPLATE = """\
---
pretty_name: TopVenues Cybersecurity Corpus
license: odc-by
language:
- en
task_categories:
- text-retrieval
tags:
- cybersecurity
- security
- bibliography
- literature-review
- dblp
size_categories:
- 100K<n<1M
configs:
- config_name: default
  data_files:
  - split: train
    path: train-*.parquet
---

# TopVenues Cybersecurity Corpus

A reproducible, cybersecurity-focused bibliographic corpus for literature
reviews: {total:,} papers ({year_min}–{year_max}) across {n_events}
cybersecurity venues, with {n_abstracts:,} abstracts and a BibTeX entry for
every record.

- **Foundational paper:** [TopVenues: A Reproducible Corpus and Tooling
  Substrate for Cybersecurity Literature Reviews
  (arXiv:2606.18320)](https://arxiv.org/abs/2606.18320). That paper reports an
  earlier, smaller frozen snapshot; this dataset is the expanded tool snapshot.
- **Code / tool:** <https://github.com/sidneibarbieri/topvenues-tool>
- **Pinned source of truth:** the gzipped SQLite snapshot shipped with the
  tool; this dataset is a faithful Parquet export of the same frozen state.

## Usage

```python
from datasets import load_dataset

corpus = load_dataset("{repo_id}", split="train")

security = corpus.filter(lambda paper: paper["area"] == "security")
```

## Scope and curation

The corpus is deliberately cybersecurity-only: 17 security venues plus 3
survey venues that anchor security literature reviews. Keeping the scope
focused (rather than mixing in off-topic AI, systems, or networking venues)
is what keeps abstract coverage high. The {security_total:,}-paper security
core carries {security_abstracts:,} abstracts ({security_pct:.1f}% coverage);
the remaining gaps are structural (e.g. Springer-hosted ESORICS and
publisher-gated recent proceedings) and are reported, not hidden. Records
without an abstract stay searchable by title, venue, year, author, and DBLP
key.

## Schema

| Column | Description |
| --- | --- |
| `paper_id` | Stable identifier (DBLP-derived) |
| `key` | DBLP key |
| `title` | Paper title |
| `authors` | Author list as a single string |
| `event` | Canonical venue name (normalized) |
| `venue` | Venue string as recorded by DBLP |
| `area` | Research area (`security`, `ai`, `networks`, `mobile`, `systems`, `cross-area`) |
| `year` | Publication year |
| `paper_type` | Record type (article, proceedings, …) |
| `pages` | Page range |
| `url` / `ee` | DBLP URL / electronic edition (DOI or publisher link) |
| `abstract` | Abstract, where the curation policy backfills it |
| `bibtex` | DBLP-canonical BibTeX entry |

## Venues

{venue_table}

## Sources and licensing

Bibliographic metadata and BibTeX come from [DBLP](https://dblp.org)
(released CC0). Abstracts were collected from open scholarly sources
(Semantic Scholar, OpenAlex, CrossRef) and publisher pages; they remain the
copyright of their respective publishers and are included for research and
indexing purposes. The compilation is released under
[ODC-BY 1.0](https://opendatacommons.org/licenses/by/1-0/).

## Citation

```bibtex
@misc{{barbieri2026topvenues,
  title  = {{TopVenues: A Reproducible Corpus and Tooling Substrate for
            Cybersecurity Literature Reviews}},
  author = {{Barbieri, Sidnei and Ferraz, Agney Lopes Roth and
            Pereira J{{\\'u}}nior, Louren{{\\c{{c}}}}o Alves}},
  year   = {{2026}},
  eprint = {{2606.18320}},
  archivePrefix = {{arXiv}},
  primaryClass  = {{cs.CR}},
  url    = {{https://arxiv.org/abs/2606.18320}}
}}
```
"""


def export_hf_dataset(
    db_path: Path,
    out_dir: Path,
    repo_id: str = "sidneibarbieri/topvenues",
) -> dict:
    """Write ``train-*.parquet`` shards and ``README.md`` under ``out_dir``.

    Returns the statistics used in the card so callers can display them.
    """
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query("SELECT * FROM papers", conn)

    df["area"] = df["event"].map(area_for)
    df = df[_EXPORT_COLUMNS].sort_values(
        ["area", "event", "year", "title"]
    ).reset_index(drop=True)

    out_dir.mkdir(parents=True, exist_ok=True)
    # A fresh export owns the directory: stale shards from a previous corpus
    # would otherwise be loaded together with the new ones. Shards live at the
    # repository root because web uploads cannot carry directory paths.
    for stale in list(out_dir.glob("train-*.parquet")) + list(out_dir.glob("data/train-*.parquet")):
        stale.unlink()
    # Sharded to stay well under per-file web-upload limits and to let the
    # Hub viewer stream row groups independently.
    rows_per_shard = 12_000
    shard_count = max(1, -(-len(df) // rows_per_shard))
    parquet_paths = []
    for shard_index in range(shard_count):
        shard = df.iloc[shard_index * rows_per_shard:(shard_index + 1) * rows_per_shard]
        path = out_dir / f"train-{shard_index:05d}-of-{shard_count:05d}.parquet"
        shard.to_parquet(path, index=False)
        parquet_paths.append(path)

    has_abstract = df["abstract"].notna() & (df["abstract"] != "")
    security = df["area"] == "security"
    stats = {
        "total": len(df),
        "n_events": df["event"].nunique(),
        "n_abstracts": int(has_abstract.sum()),
        "year_min": int(df["year"].min()),
        "year_max": int(df["year"].max()),
        "security_total": int(security.sum()),
        "security_abstracts": int((security & has_abstract).sum()),
        "parquet_paths": parquet_paths,
    }
    stats["security_pct"] = 100.0 * stats["security_abstracts"] / stats["security_total"]

    venue_rows = ["| Venue | Area | Papers | Abstracts |", "| --- | --- | ---: | ---: |"]
    grouped = df.assign(has_abstract=has_abstract).groupby("event", sort=False)
    summary = grouped.agg(
        area=("area", "first"), papers=("title", "size"), abstracts=("has_abstract", "sum")
    ).sort_values("papers", ascending=False)
    for event, row in summary.iterrows():
        venue_rows.append(
            f"| {event} | {row['area']} | {row['papers']:,} | {int(row['abstracts']):,} |"
        )

    card = _CARD_TEMPLATE.format(venue_table="\n".join(venue_rows), repo_id=repo_id, **stats)
    (out_dir / "README.md").write_text(card, encoding="utf-8")
    return stats
