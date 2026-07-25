# TopVenues SF Reviewer Guide

This release is the executable artifact for the SBSeg 2026 Salão de Ferramentas paper. Its only evaluation object is the immutable `security-20` profile.

## What the release verifies

- 20,305 bibliographic records from 20 declared security and security-relevant venues;
- 17,491 abstract-enriched records and BibTeX for every record;
- the compressed SQLite snapshot SHA-256;
- 238 automated tests; and
- local FTS5 ranked search and a BibTeX export.

The artifact is a corpus-construction and review-workflow tool. It does not claim to reproduce the measurements of the separate accepted full paper.

## Reproduce from a fresh clone

```bash
git clone --branch sbseg2026-sf-submission https://github.com/sidneibarbieri/topvenues-tool.git
cd topvenues-tool
bash reproduce.sh
```

The command creates an isolated Python environment, verifies the immutable snapshot, materializes a disposable database, runs 238 tests, builds FTS5, exercises substring and ranked search, and exports a BibTeX sample. It needs network access only to install Python dependencies on the first run; all validation after installation uses committed files.

Expected final line:

```text
Profile security-20 reproduced successfully
```

## Inspect the tool

```bash
source .venv/bin/activate
python -m streamlit run web/app.py
```

Open `http://localhost:8501`, inspect coverage, run a ranked search, and export a result set as BibTeX, CSV, or JSON.

## Scope and limitations

The profile declares its venue identifiers in `profiles/security-20/config.yaml` and its snapshot identity in `data/profiles/security-20/manifest.json`. Venue names are part of the scientific scope and intentionally remain visible. Records lacking an abstract remain available for metadata and BibTeX workflows, but abstract-dependent queries must not treat them as abstract-enriched.

Live collection and enrichment are optional maintenance operations. They depend on external sources and are not required to validate this release. The public Hugging Face export is a Parquet representation of the same profile; its card records the snapshot SHA-256 and source tag.

## Reviewer boundary

No API key, publisher credential, paid service, GPU, or institutional access is needed for the reproduction command. The repository contains no author-private data or operational traces. Tool code is MIT licensed; third-party abstract text remains subject to its original source terms.
