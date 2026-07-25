# TopVenues — Artifact

TopVenues is an open-source tool that builds a declared, reproducible corpus of
top cybersecurity publications and turns it into a measurement substrate for
literature reviews. It accompanies the paper *"TopVenues: A Reproducible Corpus
and Tooling Substrate for Cybersecurity Literature Reviews."*

The paper frames corpus construction as a reproducibility problem and solves it
with a DBLP-backed, monotonically enriched, checksum-verified SQLite snapshot.
Its sole denominator is the immutable `submitted-11` profile: 9,925 records from
11 venues. Over that object, the accepted paper reports a 29.2% arXiv match rate,
a median lead of 154 days, and a 16.5x relative risk (2.5x conventional lift) at
about 90% recall for the readiness filter.

This development tree also contains a separate `security-20` release candidate
(20,305 records), a broad historical `full-40` snapshot (120,628 records), and a
link to the independently refreshed Hugging Face dataset (144,785 Dataset Viewer
rows on 2026-07-22). None of those three objects is a denominator for the
accepted paper.

| Object | Scientific role | Publication status |
| --- | --- | --- |
| `submitted-11` | Immutable accepted-paper denominator | Frozen; public source commit recorded in the manifest |
| `security-20` | Expanded security-oriented tool candidate | Local release candidate; no public commit/tag yet |
| `full-40` | Broad cross-area historical catalog | Frozen historical object; not paper evidence |
| [Hugging Face](https://huggingface.co/datasets/sidneibarbieri/topvenues) | Mutable living export | Public and independently refreshed; never paper evidence |

## Readme Structure

This document follows the artifact-evaluation template: project summary,
structure, considered badges, basic information, dependencies, security
concerns, installation, a minimal test, experiments (one subsection per paper
claim), and the license. The repository is organized as follows.

| Path | Purpose |
|------|---------|
| `src/` | pipeline, database, models, extractors, CLI |
| `web/` | Streamlit exploration interface |
| `tests/` | pytest suite |
| `scripts/` | measurement scripts (`early_signal_study.py`, `readiness_study.py`, `readiness_baselines.py`) |
| `profiles/` | closed configurations for `submitted-11`, `security-20`, and `full-40` |
| `data/profiles/` | immutable profile snapshots and manifests |
| `data/dataset/papers.db.gz` | default working snapshot, byte-identical to the unreleased `security-20` candidate |
| `data/dataset/arxiv_cs_cr_2022_2026.jsonl.gz` | committed compressed arXiv snapshot for the measurement claims |
| `config.yaml` | mutable default scope for the `security-20` candidate |
| `reproduce.sh` | one-command reproduction of `submitted-11` by default; named profiles require `--profile` |
| `Dockerfile`, `docker-compose.yml` | self-contained execution environment |

## Considered Badges

The badges considered for evaluation are **Available**, **Functional**,
**Sustainable**, and **Reproducible**.

- **Available** — the `submitted-11` paper artifact has public source lineage,
  committed evidence, this README, and an MIT license. `security-20` is not yet
  claimed as publicly available because its exact source and snapshot lack a
  public commit/tag.
- **Functional** — the CLI, the web interface, and the test suite execute
  locally and expose the artifact's features.
- **Sustainable** — a modular, typed Python package with 328 executable
  tests and in-code documentation; each paper claim maps to a named script.
- **Reproducible** — named profile manifests verify snapshot identity offline;
  `reproduce.sh` defaults to the immutable `submitted-11` denominator and
  re-derives the accepted-paper measurements. Other named profiles are checked
  only when selected with `--profile`.

## Basic Information

- Operating system: Linux or macOS (Windows via WSL2 or Docker).
- Interpreter: Python 3.11 or 3.12.
- Hardware: about 2 GB RAM and 1 GB of free disk; no GPU.
- All claim verification runs offline from the committed snapshots and contacts
  no external service. Network access is needed only to install dependencies on
  first run (or use the provided Docker image) and for the optional pipeline
  refresh.
- The scientific denominator for the accepted paper is only
  `data/profiles/submitted-11/papers.db.gz` (9,925 records). Its manifest fixes
  the checksum and counts.
- The default `data/dataset/papers.db.gz` is the 20,305-record `security-20`
  candidate. It is not the paper denominator and is not yet a public release.
- CSV, JSON, BibTeX, Parquet, and Hugging Face views are derived or living
  exports, not independent sources of paper claim values. A new release needs a
  new manifest, checksum, commit/tag, and updated claims.

## Dependencies

- Runtime and test dependencies are declared in `requirements.txt`: `arxiv`,
  `beautifulsoup4`, `click`, `httpx`, `pandas`, `pydantic`, `pyyaml`, `rich`,
  plus `pytest` and `pytest-asyncio`.
- Optional web-interface dependencies are declared in `requirements-web.txt`:
  `streamlit` and `watchdog`.
- Python 3.11 or newer. Optional: Docker with the Compose plugin.
- No third-party benchmarks are required. Named corpus snapshots live under
  `data/profiles/`; the default candidate and arXiv input live under
  `data/dataset/` and are read directly.

## Security Concerns

The artifact poses no risk to evaluators. It runs locally, reads committed
read-only snapshots, performs no network access during claim verification,
executes no untrusted input, and requires no elevated privileges. The optional
pipeline-refresh commands contact public scholarly services (DBLP, OpenAlex,
CrossRef, Semantic Scholar) and arXiv over HTTPS only.

## Installation

From the supplied artifact directory, the default command evaluates the
accepted paper's immutable `submitted-11` profile:

```bash
bash reproduce.sh
```

`reproduce.sh` creates `.venv/`, installs the declared verification dependencies,
verifies and materializes `submitted-11`, runs the test and search/export checks,
and re-derives the paper's early-signal and readiness results. A Docker
alternative needs no local Python:

```bash
docker compose run --rm app bash reproduce.sh
```

The `security-20` candidate is optional and is not yet available from an exact
public commit or tag. From a supplied release-candidate directory or archive,
select it explicitly:

```bash
bash reproduce.sh --profile security-20
```

This profile-specific run verifies the manifest, corpus counts, test suite, and
search/export paths, then skips the paper-specific measurements because their
denominator is `submitted-11`. `full-40` is selected analogously with
`--profile full-40`.

The publicly frozen source lineage for `submitted-11` can be inspected
separately:

```bash
git clone https://github.com/sidneibarbieri/topVenues.git
cd topVenues
git checkout arxiv-2606.18320
```

Do not expect that public tag to contain the later `security-20` candidate.

## Minimal Test

Verify the accepted paper's denominator first:

```bash
.venv/bin/python scripts/verify_profile_snapshot.py --profile submitted-11
.venv/bin/python -m src.cli --profile submitted-11 stats
```

Expected: 9,925 records, 9,911 abstracts, 9,924 BibTeX entries, and 11 venues.
The manifest check must succeed before any paper result is discussed.

For the expanded local release candidate:

```bash
.venv/bin/python -m src.cli --profile security-20 stats
.venv/bin/python -m pytest -q
```

Expected: `stats` prints 20,305 papers across 20 venues with 17,491 abstracts and
20,305 BibTeX entries; all 328 tests pass. This confirms the `security-20`
candidate can be materialized and the package is functional; it does not verify
the accepted paper's denominator.

## Experiments

### Accepted-paper snapshot identity

- Command: `.venv/bin/python scripts/verify_profile_snapshot.py --profile submitted-11`
- Expected: 9,925 papers, 11 venues, and SHA-256
  `0f4dbaa97d0cf39abd2340adb3280643df090b5de9cd1a29bff39a0b53ef64cd`.
- Boundary: this command verifies the immutable denominator. The public frozen
  source lineage is recorded in the manifest and at the
  [`arxiv-2606.18320` tag](https://github.com/sidneibarbieri/topVenues/releases/tag/arxiv-2606.18320).

### Accepted-paper experiments (default)

`bash reproduce.sh` selects `submitted-11` when no profile is supplied. After
dependency installation it verifies the snapshot SHA-256 and runs the claims
below offline. The final status is `Profile submitted-11 reproduced
successfully`.

#### Paper claim 1 — Corpus coverage

- Command: `.venv/bin/python -m src.cli --profile submitted-11 stats`
- Expected: 9,925 papers; 9,911 abstracts; 9,924 BibTeX entries; 11 venues.
- Time and resources: under 5 seconds, under 1 GB RAM and disk.

#### Paper claim 2 — Reproducible snapshot and integrity tests

- Command: `.venv/bin/python -m pytest -q` (also run inside `reproduce.sh`)
- Expected: 328 tests pass, including the monotonic-enrichment (COALESCE)
  invariant; `reproduce.sh` also prints the snapshot SHA-256.
- Time and resources: under 30 seconds, under 1 GB RAM and disk.

#### Paper claim 3 — Query and export execution

- Command: `bash reproduce.sh` (latency and export stages)
- Expected: the 11-trial benchmark returns substring and BM25-ranked results;
  the topic-filtered BibTeX sample is non-empty. Timing is host-dependent and
  is reported rather than asserted.
- Time and resources: under 10 seconds, under 1 GB RAM and disk.

#### Paper claim 4 — Early-signal measurement

- Command: `.venv/bin/python scripts/early_signal_study.py --profile submitted-11`
- Expected: 742 of 2,537 scoped papers (29.2%) have a matching arXiv preprint,
  with a median lead time of 154 days.
- Time and resources: under 30 seconds offline from the committed arXiv
  snapshot; under 2 GB RAM. Re-harvesting from arXiv is optional and needs
  network access.

#### Paper claim 5 — Scientific-readiness filter and baselines

- Commands: `.venv/bin/python scripts/readiness_study.py --profile submitted-11`
  and `.venv/bin/python scripts/readiness_baselines.py --profile submitted-11`
- Expected: prior top-tier authorship yields a 16.5x relative risk (2.5x conventional lift) at 90%
  recall (Jaccard 0.6); the baselines show this exceeds prolific-author and
  random-author controls, and the first/senior-author variants trade precision
  for recall.
- Time and resources: under 10 seconds, under 2 GB RAM.

### Optional profile verification

`bash reproduce.sh --profile security-20` verifies the 20,305-record local
release candidate; `bash reproduce.sh --profile full-40` verifies the
120,628-record historical profile. Both runs check the selected manifest and
counts, execute the common tests and search/export checks, and explicitly skip
early-signal and readiness measurements. Neither run reproduces a paper claim.

## License

MIT. See `LICENSE`.
