# Data Directory

This directory contains local data used by the TopVenues artifact.

## Canonical Dataset Snapshot

- `dataset/papers.db.gz`: committed compressed SQLite snapshot — the pinned
  source of truth. On first launch the tool materializes `dataset/papers.db`
  from it automatically.
- `dataset/papers.db`: working SQLite database (derived, not committed).

Current verified snapshot:

- 20,305 papers across 20 cybersecurity venues (2017–2026).
- 17,491 papers with abstracts overall; 14,290 of 16,806 papers in the
  security core have abstracts (85.0%).
- 20,305 papers with BibTeX (100%).

The Parquet package prepared for the Hugging Face Hub is regenerated
reproducibly from this snapshot via `python -m src.cli export-hf`. Publication
and the public URL must be validated before they are claimed in the paper.

## Reproducibility Inputs

- `dblp/`: DBLP XML dump and DTD used for offline venue materialization and
  BibTeX enrichment.
- `json/`: DBLP venue/year JSON downloads.
- `cache/`: abstract-fetch cache.
- `checkpoints/`: long-running pipeline checkpoints.

## Archive

- `archive/`: historical data package retained for traceability. Do not cite it
  as the current corpus unless it is explicitly revalidated.

## Maintenance Rule

Generated logs and Python caches should not be kept here. Dataset snapshots,
DBLP inputs, JSON downloads, cache files, and checkpoints are retained because
they support repeatability and artifact evaluation.
