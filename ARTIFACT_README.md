# TopVenues — Artifact

TopVenues is an open-source tool that builds a declared, reproducible corpus of
top cybersecurity publications and turns it into a measurement substrate for
literature reviews. It accompanies the paper *"TopVenues: A Reproducible Corpus
and Tooling Substrate for Cybersecurity Literature Reviews."*

The paper frames corpus construction as a reproducibility problem and solves it
with a DBLP-backed, monotonically enriched, checksum-verified SQLite snapshot.
Using that snapshot as a fixed denominator, it measures that 29.0% of recent
top-tier security papers appear as arXiv preprints a median of about five months
before publication, and that a tunable author-track-record filter triages those
preprints at up to a 16.5x relative risk (2.5x conventional lift) at 90% recall. This artifact reproduces
those claims offline from committed snapshots.

## Readme Structure

This document follows the artifact-evaluation template: project summary,
structure, considered badges, basic information, dependencies, security
concerns, installation, a minimal test, experiments (one subsection per paper
claim), and the license. The repository is organized as follows.

| Path | Purpose |
|------|---------|
| `src/` | pipeline, database, models, extractors, CLI |
| `web/` | Streamlit exploration interface |
| `tests/` | pytest suite (317 tests) |
| `scripts/` | measurement scripts (`early_signal_study.py`, `readiness_study.py`, `readiness_baselines.py`) |
| `data/dataset/papers.db.gz` | committed compressed SQLite corpus snapshot |
| `data/dataset/arxiv_cs_cr_2022_2026.jsonl.gz` | committed compressed arXiv snapshot for the measurement claims |
| `config.yaml` | declared corpus scope and study windows |
| `reproduce.sh` | one-command verification of every claim |
| `Dockerfile`, `docker-compose.yml` | self-contained execution environment |

## Considered Badges

The badges considered for evaluation are **Available**, **Functional**,
**Sustainable**, and **Reproducible**.

- **Available** — public repository with source, committed snapshots, this
  README, and an MIT license.
- **Functional** — the CLI, the web interface, and the test suite execute
  locally and expose the artifact's features.
- **Sustainable** — a modular, typed Python package with a 317-test suite and
  in-code documentation; each paper claim maps to a named script.
- **Reproducible** — `reproduce.sh` re-derives every headline claim from a
  fresh clone, offline, using only the committed snapshots.

## Basic Information

- Operating system: Linux or macOS (Windows via WSL2 or Docker).
- Interpreter: Python 3.11 or 3.12.
- Hardware: about 2 GB RAM and 1 GB of free disk; no GPU.
- All claim verification runs offline from the committed snapshots and contacts
  no external service. Network access is needed only to install dependencies on
  first run (or use the provided Docker image) and for the optional pipeline
  refresh.
- The scientific denominator for the paper is the committed SQLite snapshot.
  CSV, JSON, BibTeX, and Parquet views are generated from that denominator;
  they are not independent sources of claim values. Publishing a refreshed
  corpus requires a new snapshot checksum and updated reported counts.

## Dependencies

- Runtime and test dependencies are declared in `requirements.txt`: `arxiv`,
  `beautifulsoup4`, `click`, `httpx`, `pandas`, `pydantic`, `pyyaml`, `rich`,
  plus `pytest` and `pytest-asyncio`.
- Optional web-interface dependencies are declared in `requirements-web.txt`:
  `streamlit` and `watchdog`.
- Python 3.11 or newer. Optional: Docker with the Compose plugin.
- No third-party benchmarks are required. The corpus and arXiv snapshots ship
  in `data/dataset/` as gzip files and are read directly.

## Security Concerns

The artifact poses no risk to evaluators. It runs locally, reads committed
read-only snapshots, performs no network access during claim verification,
executes no untrusted input, and requires no elevated privileges. The optional
pipeline-refresh commands contact public scholarly services (DBLP, OpenAlex,
CrossRef, Semantic Scholar) and arXiv over HTTPS only.

## Installation

```bash
git clone https://github.com/sidneibarbieri/topvenues-tool.git
cd topvenues-tool
bash reproduce.sh
```

`reproduce.sh` creates `.venv/`, installs the declared verification dependencies, materializes
`papers.db` from the committed `papers.db.gz`, and then verifies every claim. A
Docker alternative needs no local Python:

```bash
docker compose run --rm app bash reproduce.sh
```

If your shell is already inside the `TopVenues` directory, skip the `cd` step.

## Minimal Test

```bash
.venv/bin/python -m src.cli stats     # corpus statistics
.venv/bin/python -m pytest -q         # test suite
```

Expected: `stats` prints 20,305 papers across 20 venues with 17,491 abstracts and
20,305 BibTeX entries; the suite reports `317 passed` in about one second. This
confirms the snapshot bootstrapped and the package is functional.

## Experiments

`bash reproduce.sh` runs every claim below in one or two minutes (after dependency
installation), offline, from the committed snapshots, and prints the snapshot
SHA-256 for byte-stability. Each claim can also be reproduced on its own.

### Claim 1 — Corpus coverage

- Command: `.venv/bin/python -m src.cli stats`
- Expected: 20,305 papers; 17,491 abstracts overall; 14,290 abstracts in the
  16,806-paper security core (85.0%); 20,305 BibTeX (100%); 20 cybersecurity venues
  across 2017--2026.
- Time and resources: under 5 seconds, under 1 GB RAM and disk.

### Claim 2 — Reproducible snapshot and integrity tests

- Command: `.venv/bin/python -m pytest -q` (also run inside `reproduce.sh`)
- Expected: 317 tests pass, including the monotonic-enrichment (COALESCE)
  invariant; `reproduce.sh` also prints the snapshot SHA-256.
- Time and resources: under 30 seconds, under 1 GB RAM and disk.

### Claim 3 — Query and export performance

- Command: `bash reproduce.sh` (latency and export stages)
- Expected on the reference Apple M4 Max host: the 11-trial benchmark reports
  substring medians of 21--37 ms and BM25-ranked medians of
  0.8--15 ms on the full corpus; a topic-filtered BibTeX export completes
  in under one second.
- Time and resources: under 10 seconds, under 1 GB RAM and disk.

### Claim 4 — Early-signal measurement

- Command: `.venv/bin/python scripts/early_signal_study.py`
- Expected: 29.0% of 2024--2025 core-venue papers have a matching arXiv
  preprint, with a median lead time near 149 days.
- Time and resources: under 30 seconds offline from the committed arXiv
  snapshot; under 2 GB RAM. Re-harvesting from arXiv is optional and needs
  network access.

### Claim 5 — Scientific-readiness filter and baselines

- Commands: `.venv/bin/python scripts/readiness_study.py` and
  `.venv/bin/python scripts/readiness_baselines.py`
- Expected: prior top-tier authorship yields a 16.5x relative risk (2.5x conventional lift) at 90%
  recall (Jaccard 0.6); the baselines show this exceeds prolific-author and
  random-author controls, and the first/senior-author variants trade precision
  for recall.
- Time and resources: under 10 seconds, under 2 GB RAM.

## License

MIT. See `LICENSE`.
