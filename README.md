# TopVenues

**A reproducible bibliographic explorer for configured security research sources.**

Paper: [arXiv:2606.18320](https://arxiv.org/abs/2606.18320) ·
Dataset export: generated locally; public Hub validation pending ·
License: MIT

> **Lineage.** This repository is the actively developed tool. The exact
> corpus and code measured by the companion paper
> [arXiv:2606.18320](https://arxiv.org/abs/2606.18320) are frozen at
> [`topVenues@arxiv-2606.18320`](https://github.com/sidneibarbieri/topVenues/releases/tag/arxiv-2606.18320)
> and are not modified here. This tree extends that artifact with a larger
> snapshot (144,785 papers / 40 venues), BM25 ranked search, tier-weighted
> author analytics, and the Hugging Face dataset export.

`TopVenues` builds a curated, searchable SQLite dataset for a declared
computer-security literature scope. It downloads
metadata from DBLP, backfills abstracts where reliable public sources expose
them, and exposes a fast full-text search interface for
researchers, students and reviewers preparing literature reviews.

The current released dataset snapshot covers **144,785 papers** across **40
canonical venues**, with **17,603 abstracts** and **144,785 BibTeX records**.
Abstracts are intentionally backfilled by policy rather than scraped
indiscriminately; the full bibliographic denominator is the SQLite snapshot.

---

## Indexed venues

The snapshot spans 40 normalized venues grouped by research area:

- **Security:** ACM CCS, IEEE S&P, USENIX Security, NDSS, ACM ASIA CCS,
  IEEE EURO S&P, ACSAC, ACM SACMAT, ACM CODASPY, ESORICS, RAID, IEEE CNS,
  ACM WiSec, USENIX WOOT, IEEE SaTML, ACM AISec, TrustCom.
- **Networks, systems, and mobile:** HotNets, ACM SIGCOMM, USENIX NSDI,
  ACM IMC, ACM SIGMETRICS, USENIX ATC, ACM EuroSys, ACM MobiCom,
  ACM MobiSys, ACM SenSys, ACM HotMobile.
- **AI/ML/NLP:** NeurIPS, ICML, ICLR, AAAI, IJCAI, ACM KDD, ACL, EMNLP,
  NAACL.
- **Surveys and journals:** ACM Computing Surveys, IEEE Communications
  Surveys & Tutorials, Foundations and Trends in Privacy and Security.

The set is declared in `config.yaml`. Adding a venue also requires explicit
normalization, area, and tier mappings; see *Extending* below.

---

## Quick start

```bash
git clone https://github.com/sidneibarbieri/topvenues-tool.git
cd topvenues-tool
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

That's it — the repository ships with the full SQLite database as a
compressed snapshot (`data/dataset/papers.db.gz`, 96.3 MiB). On first launch
the application transparently materializes `data/dataset/papers.db` (302.2 MiB)
from that snapshot, so there is **no manual import step**: 144,785 papers,
17,603 abstracts and 144,785 BibTeX entries are available immediately.

The released corpus is pinned by the compressed SQLite snapshot;
`reproduce.sh` and the paper claims read that snapshot. Tabular exports are
prepared for publication on the Hugging Face Hub (see *Hugging Face dataset export* below)
and regenerated from the same frozen database. A refreshed corpus should be
published as a new snapshot with a new checksum and updated reported counts,
rather than silently changing the submission denominator.

When a newer snapshot lands upstream and you want to refresh your local
copy explicitly:

```bash
python3 -m src.cli refresh-db
```

### Web interface (recommended)

If your shell prompt already ends in `topvenues-tool`, do not run
`cd topvenues-tool` again; start from the commands below.

```bash
python3 -m streamlit run web/app.py
```

If the optional web dependencies are not installed yet, run:

```bash
python3 -m pip install -r requirements-web.txt
```

Open <http://localhost:8501>. Main pages:

- **Overview** — headline claims, reproduction command, evidence
  table and scientific findings.
- **Search** — full-text filters on title, abstract, authors, topic; venue,
  year, paper class (SoK / Survey / Poster / Workshop / Short / Journal /
  Article), abstract-length and BibTeX filters; sortable, paginated table
  that shows an abstract preview and the `\cite{...}` command for each row.
  CSV / JSON / `.bib` export.
- **Insights** — distributions by venue, year, and class; abstract and BibTeX
  coverage; and venue-stratified author visibility by topic or area.
- **Pipeline** — run download / consolidate / extract / bibtex directly
  from the UI.

### Command line

```bash
python3 -m src.cli download         # fetch DBLP JSON for all venues and years
python3 -m src.cli download --event acsac --event satml --year 2025  # scoped refresh
python3 -m src.cli materialize-from-dump  # offline DBLP JSON materialization
python3 -m src.cli materialization-status             # configured vs downloaded JSON
python3 -m src.cli consolidate      # merge into SQLite (idempotent)
python3 -m src.cli extract          # fetch missing abstracts (rate-limited)
python3 -m src.cli backfill-abstracts --event ACSAC      # DOI-API backfill
python3 -m src.cli bibtex           # fetch BibTeX entries from DBLP
python3 -m src.cli run-all          # download + consolidate + extract + bibtex

python3 -m src.cli search --title "SOC" --author "Sekar" --abstract "LLM"
python3 -m src.cli search --tech "blockchain" --year 2024
python3 -m src.cli export --format bibtex --tech "intrusion detection" -o intrusion.bib
python3 -m src.cli stats
```

### Topic trends

`trends` traces a topic over time — papers per year, the topic's share of
each year's corpus, and the venues that publish it most. Share normalizes by
yearly corpus size, so corpus growth does not masquerade as topic growth:

```bash
python3 -m src.cli trends --topic "LLM" --since 2019
python3 -m src.cli trends --topic "ransomware" --area security
```

### Ranked search (BM25 / FTS5)

Substring filters answer "which papers mention X"; ranked search answers
"which papers are *about* X". `--rank` searches an SQLite FTS5 index over
title, abstract, and authors with BM25 scoring (title hits weighted 5×,
author hits 2×, abstract hits 1×), best match first:

```bash
python3 -m src.cli build-fts                       # one-time, ~2 s on the full corpus
python3 -m src.cli search --rank "memory corruption mitigations" --limit 20
python3 -m src.cli search --rank "fuzz*" --year 2025 --award
```

The index is derived state: it is built locally on demand (a first
`search --rank` builds it automatically), is kept in sync by triggers on
every upsert, and is not part of the published snapshot. Ranked queries
answer in single- to low-double-digit milliseconds on the 145k-paper corpus. Multi-word
queries use AND-of-tokens semantics; a trailing `*` enables prefix matching.

### Hugging Face dataset export

`export-hf` materializes the corpus as a Parquet file plus a generated
dataset card, ready to upload to the Hub:

```bash
python3 -m src.cli export-hf                       # writes data/hf-dataset/
hf upload-large-folder sidneibarbieri/topvenues --repo-type dataset data/hf-dataset
```

The generated dataset is a faithful export of the pinned SQLite snapshot used
by the companion tool manuscript. Do not rely on
`load_dataset("sidneibarbieri/topvenues")` until the public Hub URL and Dataset
Viewer have been validated anonymously. The earlier arXiv paper reports a
smaller frozen snapshot; the repository lineage above keeps the two objects
separate.

### Paper-award metadata

Paper-award labels (Best Paper / Distinguished Paper) are collected per venue into
`data/awards/`, each record carrying the official award-page URL it came from:

```bash
python3 scripts/collect_acsac_awards.py   # ACSAC distinguished/outstanding, from the ACSAC archive
python3 scripts/import_top4_awards.py      # IEEE S&P, ACM CCS, NDSS, USENIX (from data/awards/sources/)
python3 scripts/award_coverage.py          # join awards to the corpus; report matched/unmatched
```

`award_coverage.py` joins each award to a corpus paper by normalized title within
venue, writes the matches to `data/awards/award_corpus_matches.tsv`, and prints
honest gaps (an award whose paper is not in the corpus — e.g. a year outside the
corpus range — is reported as unmatched, never silently dropped).

Awards are kept intentionally separate from the DBLP `papers` table: a paper can
exist in the corpus without an award, and every award label stays source-backed.
The `search` command annotates results with awards and can filter to winners:

```bash
python3 -m src.cli search --award --year 2025         # only award-winning papers
python3 -m src.cli search --tech "fuzzing" --award    # award winners about fuzzing
```

### BibTeX & LaTeX integration

Every paper carries the BibTeX entry that DBLP would serve via its API,
plus a derived `\cite{cite_key}` snippet. The web UI shows both inline;
the **Search** page exports a ready-to-use `.bib` for the current
result set. Drop it into your LaTeX project and `\cite{…}` away.

`TopVenues` ships **three** strategies for populating the `bibtex`
column. Pick whichever fits your situation:

| Command | Source | Time | Output | When to use |
| ------- | ------ | ---- | ------ | ----------- |
| `bibtex-from-dump` | DBLP XML dump | ~10 min one-off | DBLP-canonical, with crossref-resolved `editor` / `booktitle` | **Recommended.** Single 1 GB download, then offline. |
| `bibtex-local` | Existing DB fields | seconds | Minimal but valid (no `volume`/`number`) | No internet, or DBLP throttling. |
| `bibtex` | DBLP per-record API | hours (rate-limited) | DBLP-canonical | Filling a handful of new papers. |

```bash
# One-off, gold-standard: ~10 min, 100% coverage
python3 -m src.cli bibtex-from-dump

# Instant offline fallback: zero network, ~95% completeness
python3 -m src.cli bibtex-local

# Trickle fill via API (use --concurrency 2 to stay under DBLP's rate limit)
python3 -m src.cli bibtex --concurrency 2
```

The DB column is set-once-keep: re-running any command never overwrites
existing entries unless you explicitly pass `--overwrite` (only
available on `bibtex-local`). Combining commands works as expected:
run `bibtex-local` for instant coverage, then run `bibtex-from-dump`
later to upgrade entries to DBLP-canonical when you have the bandwidth.

### Incremental updates

The pipeline is fully incremental. Re-running `download → consolidate` next
year (or after a venue posts new proceedings) only fetches what is missing and
preserves every existing abstract via SQL `COALESCE`. To pick up a new year,
just bump `year_start` in `config.yaml` or leave it on the default — it
auto-extends to the current calendar year.

For controlled expansion, scope the download to the venue keys you are adding:

```bash
python3 -m src.cli download --event satml --event esorics
python3 -m src.cli materialize-from-dump --event satml --event esorics
python3 -m src.cli consolidate
python3 -m src.cli backfill-abstracts --event "ACSAC"
python3 -m src.cli extract
python3 -m src.cli bibtex-local
python3 -m src.cli write-snapshot
```

Treat the compressed SQLite snapshot as the published denominator. For large
venue expansion, prefer `materialize-from-dump`: it parses `data/dblp/dblp.xml.gz`
locally and avoids DBLP API rate limits. The live `download` command remains
useful for small, fresh updates.

---

## Architecture

```
src/
  models.py            Pydantic DTOs (Paper, Configuration, SearchFilters,
                       AbstractImportResult, PaperClass)
  config.py            YAML configuration loader
  collector.py         Orchestrator (download → consolidate → extract)
  downloader.py        Async DBLP JSON downloader with circuit breaker
  consolidator.py      Merges JSON files into deduplicated Paper objects
  database.py          SQLite layer — single source of truth
  abstract_fetcher.py  Parallel fallback: Semantic Scholar / OpenAlex / CrossRef
  bibtex_fetcher.py    Concurrent DBLP .bib fetcher with retry / backoff
  event_normalizer.py  Venue string → canonical name (Strategy pattern)
  venue_config.py      DBLP URL strategy registry
  circuit_breaker.py   Circuit breaker for unstable upstreams
  extractors/          Per-publisher HTML extractors (xidel-based)
  cache.py             Local abstract cache (SQLite)
  checkpoint.py        Long-run resumability
  cli.py               Click CLI

web/app.py             Streamlit interface
tests/                 pytest suite
  scripts/
  api_blitz.py         Legacy concurrent API back-fill for missing abstracts
  bibtex_blitz.py      Concurrent BibTeX back-fill from DBLP
  verify_extractors.py Live integration check for publisher extractors
```

### Design highlights

- **SQLite is the single source of truth.** CSV and Pickle outputs are
  derived exports; the database survives every step of the pipeline.
- **Idempotent upsert.** Re-running `consolidate` 100× converges to the same
  state as running it once: existing abstracts are never overwritten.
- **Two-track abstract fetching.** Open APIs (Semantic Scholar, OpenAlex,
  CrossRef) are fired *in parallel* with `asyncio.as_completed` — first
  successful response wins. Publisher sites (ACM, IEEE, USENIX, NDSS) run
  *sequentially* with throttling because they sit behind Cloudflare.
- **Offline DBLP materialization.** Large corpus refreshes can use the local
  DBLP XML dump to generate the same per-venue JSON files without relying on
  live TOC API availability.
- **Strategy / Registry patterns** for both venue URL generation and event
  name normalization. Adding a new venue is purely additive.
- **Circuit breaker** wraps the DBLP downloader so a transient upstream
  outage stops cascading failures.
- **NDSS author-leak cleaner.** A comma-aware iterative matcher strips the
  `Name (Affiliation), Name (Affiliation), …` block that NDSS pages render
  before the abstract body — without ever truncating legitimate
  parentheticals like `Industrial Control Systems (ICS), …`.

---

## Configuration

`config.yaml` (abbreviated below; the released file declares all 40 venues):

```yaml
year_start: 2019                       # auto-extends to current year
events: [ccs, asiaccs, uss, ndss, sp]  # excerpt
batch_size: 10
acm_wait_min: 60.0                     # throttle window for publisher scrapers
acm_wait_max: 300.0
cache_enabled: true
cache_ttl_hours: 168
```

---

## Extending

To add a new venue:

1. Add the short identifier to `Configuration.events` and `EventType` in
   `src/models.py`.
2. Register a `VenueURLStrategy` in `src/venue_config.py` (point it at the
   DBLP page for that venue).
3. Add a normalization rule in `src/event_normalizer.py` mapping DBLP's venue
   string to the canonical display name.
4. Map the venue to a research area in `src/areas.py`.
5. Assign a declared visibility tier in `src/tiers.py`.
6. (Optional) add a publisher-specific extractor under `src/extractors/` if
   the open APIs don't cover that venue's papers reliably.

No code outside these declared registries needs to change.

---

## Development

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest                          # 299 tests
python3 -m ruff check src/ web/ tests/
```

---

## Paper and artifact preparation

Paper drafts are kept out of the public artifact under `papers/` (a local,
untracked directory) so that the released code and corpus stay independent of
any specific manuscript or venue. Artifact-evaluation notes are in
`ARTIFACT_README.md`, `REVIEWER_GUIDE.md`, and `PROJECT_STRUCTURE.md`.
Literature-review support and reference material live under `literature/`.

---

## Data sources

- [DBLP](https://dblp.org) — paper metadata
- [Semantic Scholar](https://www.semanticscholar.org/product/api) — abstracts
- [OpenAlex](https://openalex.org) — abstracts (inverted index)
- [CrossRef](https://www.crossref.org) — abstracts (JATS XML)
- Publisher sites (ACM Digital Library, IEEE Xplore, USENIX, NDSS) — abstracts

All retrieval is read-only and respects published API rate limits.

---

## Citation

If `TopVenues` helps your research, please cite it:

```bibtex
@misc{barbieri2026topvenues,
  title  = {TopVenues: A Reproducible Corpus and Tooling Substrate for
            Cybersecurity Literature Reviews},
  author = {Barbieri, Sidnei and Ferraz, Agney Lopes Roth and
            Pereira J{\'u}nior, Louren{\c{c}}o Alves},
  year   = {2026},
  eprint = {2606.18320},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CR},
  url    = {https://arxiv.org/abs/2606.18320}
}
```

GitHub's citation widget reads [CITATION.cff](CITATION.cff).

---

## Authors

**Sidnei Barbieri**, **Agney Lopes Roth Ferraz**, and
**Lourenco Alves Pereira Junior**.

Built to support systematic literature reviews and threat-landscape mapping
across the top-tier security research venues.

---

## License

MIT — see [LICENSE](LICENSE).
