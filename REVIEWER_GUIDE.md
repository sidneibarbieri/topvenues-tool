# TopVenues — Reviewer Guide

This guide is the practical entry point for reviewers who want to
inspect the TopVenues artifact.

## What TopVenues Is

TopVenues is an open-source, reproducible literature-review substrate
for cybersecurity. It combines a tool and a methodology for constructing,
refreshing, querying, and exporting venue-bounded paper collections.

The accepted paper's denominator is the immutable `submitted-11` profile
(9,925 records, 11 venues). The default development database is the distinct
`security-20` release candidate (20,305 records, 20 venues), which has not yet
been published as an exact commit or tag. `full-40` is a 120,628-record broad
historical snapshot. The public [Hugging Face dataset](https://huggingface.co/datasets/sidneibarbieri/topvenues)
is a mutable living export (144,785 Dataset Viewer rows on 2026-07-22) and is
never a paper denominator.

## What To Inspect First

1. `ARTIFACT_README.md` — artifact overview and badge mapping.
2. `profiles/README.md` — release boundary and profile-specific commands.
3. `data/profiles/submitted-11/` — accepted-paper snapshot and manifest.
4. `reproduce.sh` — single-shot reproduction of `submitted-11` by default;
   other profiles require an explicit `--profile` argument.
5. `data/dataset/arxiv_cs_cr_2022_2026.jsonl.gz` — committed preprint input for the accepted-paper measurements.
6. `src/`, `web/`, and `tests/` — implementation and executable checks.

## Minimal Verification

First verify the accepted paper's immutable denominator:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/verify_profile_snapshot.py --profile submitted-11
python -m src.cli --profile submitted-11 stats
```

Expected: the manifest check succeeds and `stats` reports 9,925 records,
9,911 abstracts, 9,924 BibTeX entries, and 11 venues. This is the only local
profile whose `paper_denominator` field is true.

Run the integrated accepted-paper reproduction with:

```bash
bash reproduce.sh --skip-install
```

Expected final status: `Profile submitted-11 reproduced successfully`. The
script verifies the 9,925-record profile manifest and counts, executes at least
328 tests plus the search/export checks, and reproduces the paper's 742/2,537
(29.2%) early-signal result, 154-day median lead, and readiness controls.
Runtime is host-dependent.

Only if evaluating the expanded tool candidate, select it explicitly:

```bash
bash reproduce.sh --profile security-20 --skip-install
```

Expected final status: `Profile security-20 reproduced successfully`. This run
checks the candidate's 20,305 records, 17,491 abstracts, 20,305 BibTeX entries,
tests, and search/export path. It explicitly skips the paper-specific
measurements because their denominator is `submitted-11`.

The broad historical profile can be checked independently:

```bash
python scripts/verify_profile_snapshot.py --profile full-40
```

Expected: 120,628 records across 40 venues. It is not used by either paper
measurement path above.

## Web Review Path

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-web.txt
streamlit run web/app.py
```

If the shell prompt already ends in `TopVenues`, skip `cd TopVenues`.
The first page, **Overview**, is the shortest evaluation path: it exposes the
claim set, the reproduction command, artifact-badge evidence and the two
measurement findings. **Search** is for corpus inspection and reference
export; **Insights** is for coverage and scope checks; **Pipeline** is only
for refreshing the corpus from live sources.

## Alternative Verification Paths

- Docker: `docker compose up` then `http://localhost:8501`.
- Manual: `pip install -r requirements.txt -r requirements-web.txt` +
  `python -m pytest -q` + `python -m src.cli --profile submitted-11 stats`.

## Positioning

TopVenues is a tool-supported methodology, not a generic paper generator or
paper search engine. Its scientific value is the reproducible construction and
preservation of a declared cybersecurity collection, auditable as a single
snapshot plus manifest. Results are valid only for the named profile from which
they were produced.

## Common Questions

**Q: Does the artifact require publisher credentials?**
No. The committed corpus and preprint snapshots make claim verification
independent of publisher portals; only the fresh-collection pipeline
(`download`, `extract`, `bibtex-from-dump`) calls external services.

**Q: Is the dataset volatile?**
The three local profile snapshots are immutable and checksum-verified. The
`security-20` object is still a local release candidate because its exact source
and snapshot have no public commit/tag. The Hugging Face dataset is intentionally
volatile and independently versioned; its live row count must not be inserted
into paper claims.

**Q: Which object reproduces the accepted paper?**
Only `submitted-11`. Do not use the default `data/dataset/papers.db.gz`,
`security-20`, `full-40`, or `load_dataset("sidneibarbieri/topvenues")` as a
substitute.

**Q: How do I extend the collection to a new venue?**
Add the venue to `config.yaml` and to the explicit URL, normalization, area,
and tier registries documented in the README. A source-specific abstract
adapter is optional.
