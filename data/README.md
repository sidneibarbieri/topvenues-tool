# Data Directory

This directory contains local data used by the TopVenues artifact. There is no
single undifferentiated "current dataset": each snapshot has a declared role.

## Snapshot map

| Path or service | Records | Role |
| --- | ---: | --- |
| `profiles/submitted-11/papers.db.gz` | 9,925 | Immutable denominator used by the accepted paper |
| `profiles/security-20/papers.db.gz` | 20,305 | Local security-oriented release candidate; not yet represented by a public commit or tag |
| `profiles/full-40/papers.db.gz` | 120,628 | Immutable broad historical catalog; not the paper denominator |
| [Hugging Face dataset](https://huggingface.co/datasets/sidneibarbieri/topvenues) | 144,785 rows in the Dataset Viewer on 2026-07-22 | Independently versioned living export; never the paper denominator |

Every local snapshot has a manifest beside it under `profiles/<profile>/`.
Run `python scripts/verify_profile_snapshot.py --profile <profile>` to check
its counts and SHA-256 without mutating it. See [`../profiles/README.md`](../profiles/README.md)
for the profile contract.

## Default development snapshot

- `dataset/papers.db.gz` is byte-identical to the local `security-20` release
  candidate. It is the default development input used by the current
  `config.yaml`; it is **not** the 9,925-record paper denominator and does not
  override `reproduce.sh`'s `submitted-11` default.
- `dataset/papers.db` is a derived working database materialized from that gzip
  and is not an independent release.

The `security-20` candidate contains 20,305 papers across 20 security and
security-relevant venues, 17,491 abstracts, and 20,305 BibTeX entries. Select it
with `bash reproduce.sh --profile security-20`; a bare `bash reproduce.sh`
selects `submitted-11`. The candidate must not be called a public release until
the exact snapshot and source are committed and tagged.

The public [Hugging Face Dataset Viewer](https://huggingface.co/datasets/sidneibarbieri/topvenues/viewer/default/train)
currently shows 144,785 rows. The Hub is refreshed independently; its count is
not expected to equal any local profile and must not be substituted into paper
claims. `python -m src.cli export-hf` produces a new local export of the selected
working snapshot but does not redefine the already published living dataset.

## Reproducibility Inputs

- `dblp/`: DBLP XML dump and DTD used for offline venue materialization and
  BibTeX enrichment.
- `json/`: DBLP venue/year JSON downloads.
- `cache/`: abstract-fetch cache.
- `checkpoints/`: long-running pipeline checkpoints.

## Archive

- `archive/`: historical data package retained for traceability. Do not cite it
  as a paper or profile denominator unless it is explicitly promoted with a
  manifest and checksum.

## Maintenance Rule

Generated logs and Python caches should not be kept here. Dataset snapshots,
DBLP inputs, JSON downloads, cache files, and checkpoints are retained because
they support repeatability and artifact evaluation.
