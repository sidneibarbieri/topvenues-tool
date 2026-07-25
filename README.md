# TopVenues

**A reproducible bibliographic explorer for configured security research sources.**

Paper: [arXiv:2606.18320](https://arxiv.org/abs/2606.18320) ·
Living dataset: [Hugging Face](https://huggingface.co/datasets/sidneibarbieri/topvenues) ·
License: MIT

> **Denominator boundary.** The accepted full paper uses only immutable
> `submitted-11`: 9,925 records from 11 venues. The Salão de Ferramentas tool
> uses the distinct immutable `security-20` profile: 20,305 records from 20
> security and security-relevant venues. `full-40` is a historical broad
> catalog, not an abstract-ready security corpus. Neither `security-20`,
> `full-40`, nor Hugging Face is a denominator for the accepted paper.

| Object | Records | Release role |
| --- | ---: | --- |
| `submitted-11` | 9,925 | Immutable accepted-paper denominator; public source commit recorded in its manifest |
| `security-20` | 20,305 | Immutable Salão de Ferramentas profile; tag `sbseg2026-sf-submission` |
| `full-40` | 120,628 | Immutable broad historical catalog |
| [Hugging Face](https://huggingface.co/datasets/sidneibarbieri/topvenues) | 20,305 | Parquet export of `security-20`, identified by its snapshot hash and release tag |

The exact corpus and code measured by the earlier companion preprint are
preserved at
[`topVenues@arxiv-2606.18320`](https://github.com/sidneibarbieri/topVenues/releases/tag/arxiv-2606.18320).
The named local profiles and their checksums are documented in
[`profiles/README.md`](profiles/README.md).

`TopVenues` builds a curated, searchable SQLite dataset for a declared
computer-security literature scope. It downloads
metadata from DBLP, backfills abstracts where reliable public sources expose
them, and exposes a fast full-text search interface for
researchers, students and reviewers preparing literature reviews.

The default local snapshot is the immutable **`security-20` release**:
**20,305 papers** across **20 security and security-relevant venues**, with **17,491 abstracts**
and **20,305 BibTeX records**.
Abstracts are intentionally backfilled by policy rather than scraped
indiscriminately. For any analysis, the denominator is the explicitly named
SQLite profile snapshot, never whichever export happens to be newest.

---

## Indexed venues

The `security-20` candidate spans 20 venues in a security-oriented profile,
grouped by role:

- **Security (17 venues):** ACM CCS, IEEE S&P, USENIX Security, NDSS,
  ACM ASIA CCS, IEEE EURO S&P, ACSAC, RAID, ESORICS, ACM CODASPY, IEEE CNS,
  ACM WiSec, ACM SACMAT, IEEE SaTML, USENIX WOOT, ACM AISec, TrustCom.
- **Security-relevant surveys (3 venues):** ACM Computing Surveys,
  IEEE Communications Surveys & Tutorials, Foundations and Trends in
  Privacy and Security.

The profile is security-oriented rather than security-exclusive: it combines
17 security venues with 3 broad survey venues relevant to security reviews.
Its abstract coverage is 86.1% overall and 85.0% on the 16,806-record security
core.

The candidate set is declared in `config.yaml`. Adding a venue also requires explicit
normalization, area, and tier mappings; see *Extending* below.

---

## Quick start

### Salão de Ferramentas release

Checkout `sbseg2026-sf-submission` to obtain the exact public tree and snapshot
used by the tool paper. The default reproduction command below intentionally
selects `security-20`; it never substitutes the companion paper's profile.

```bash
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

The release package includes the `security-20` snapshot as a
compressed snapshot (`data/dataset/papers.db.gz`, 72.7 MiB). On first launch
the application transparently materializes `data/dataset/papers.db` (232 MiB)
from that snapshot, so there is **no manual import step**: 20,305 papers,
17,491 abstracts and 20,305 BibTeX entries are available immediately.

`reproduce.sh` defaults to the Salão artifact's immutable `security-20`
profile. The explicit form below makes the denominator visible in scripts and
review reports:

```bash
bash reproduce.sh --profile security-20
```

The script verifies the 20,305-record manifest and counts, runs the common
tests and search/export checks, and deliberately skips the companion paper's
profile-specific studies. Alternative profiles must be named explicitly:

```bash
bash reproduce.sh --profile security-20
bash reproduce.sh --profile full-40
```

Those alternative runs verify the selected profile's manifest, counts, tests,
and search/export paths. They skip the paper-specific measurements because only
`submitted-11` is their valid denominator.

The three local profiles are checksum-pinned under `data/profiles/`. A refreshed
corpus must receive a new manifest, checksum, commit, and tag rather than
silently changing the paper denominator. The Hugging Face export records its
profile, checksum, and source tag in its dataset card.

### Public paper-frozen lineage

To inspect the public source lineage associated with `submitted-11`:

```bash
git clone https://github.com/sidneibarbieri/topVenues.git
cd topVenues
git checkout arxiv-2606.18320
```

That tag is not the later `security-20` Salão release documented above.

When a newer snapshot lands upstream and you want to refresh your local
copy explicitly:

```bash
python3 -m src.cli refresh-db
```

### Web interface (recommended)

If your shell prompt already ends in `topVenues`, do not run
`cd topVenues` again; start from the commands below.

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
`search --rank` builds it automatically), is kept in sync by triggers on every
upsert, and is not part of any immutable profile snapshot. Ranked queries answer
in single- to low-double-digit milliseconds on the 20k-paper candidate.
Multi-word queries use AND-of-tokens semantics; a trailing `*` enables prefix
matching.

### Hugging Face dataset export

The public dataset is available directly at
[Hugging Face](https://huggingface.co/datasets/sidneibarbieri/topvenues). It
is a Parquet export of the `security-20` snapshot, not a mutable substitute for
the companion paper's frozen data.

`export-hf` materializes the selected local working corpus as a Parquet file
plus a generated dataset card for a future Hub refresh:

```bash
python3 -m src.cli --profile security-20 export-hf --release-tag sbseg2026-sf-submission  # writes data/hf-dataset/
hf upload-large-folder sidneibarbieri/topvenues --repo-type dataset data/hf-dataset
```

The generated package records its profile and snapshot SHA. In particular,
`load_dataset("sidneibarbieri/topvenues")` must never be used to reproduce the
accepted paper's 9,925-record results.

### Paper-award metadata

Paper-award labels (Best Paper / Distinguished Paper) are collected per venue into
`data/awards/`, each record carrying the official award-page URL it came from:

```bash
python3 scripts/collect_acsac_awards.py   # ACSAC distinguished/outstanding, from the ACSAC archive
python3 scripts/import_top4_awards.py      # IEEE S&P, ACM CCS, NDSS, USENIX (from data/awards/sources/)
python3 scripts/award_coverage.py --profile submitted-11  # join against a verified profile
```

`award_coverage.py` joins each award to a corpus paper by normalized title within
venue, writes matches under `data/workspaces/<profile>/analysis/`, and prints
honest gaps (an award whose paper is not in the selected profile—e.g. ACSAC in
`submitted-11`—is reported as unmatched, never silently dropped). Use
`--output` only when a different derived TSV destination is required.

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

Treat each named profile's compressed SQLite snapshot and manifest as one
immutable release object. `data/dataset/papers.db.gz` is only the default
`security-20` candidate working input. For large venue expansion, prefer
`materialize-from-dump`: it parses `data/dblp/dblp.xml.gz` locally and avoids
DBLP API rate limits. The live `download` command remains useful for small,
fresh updates, but its output is not a release until frozen and manifested.

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

`config.yaml` (abbreviated below; the release-candidate file declares all 20 venues):

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
python3 -m pytest                          # full test suite
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
