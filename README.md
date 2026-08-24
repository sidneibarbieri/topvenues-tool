# TopVenues

TopVenues is an open-source, local-first tool for constructing and inspecting a declared corpus for cybersecurity literature reviews. The current researcher-facing release is pinned to the immutable `security-20-v2` profile.

The accepted SBSeg-SF paper remains bound to the immutable [`sbseg2026-sf-submission-r1`](https://github.com/sidneibarbieri/topvenues-tool/releases/tag/sbseg2026-sf-submission-r1) release and its `security-20` snapshot. It is preserved unchanged; do not use current counts to verify claims in that paper.

## Authors

- Sidnei Barbieri — `sidneibarbieri@gmail.com`
- Ágney Lopes Roth Ferraz — `agneyroth@gmail.com`
- Lourenço Alves Pereira Júnior — `lourenco.junior@gp.ita.br`


| Property | Value |
| --- | --- |
| Release | `v1.1.0` |
| Scope | 20 declared security and security-relevant venues |
| Records | 14,863 distinct canonical resources |
| Abstract-enriched records | 13,991 (94.1%) |
| BibTeX entries | 14,863 |
| Snapshot SHA-256 | `a25e5fce289f2ac5bbffef1ac6905279f9c11e2234c7da9e6c0a7c5a77d8ea15` |

The successor merges only exact canonical resource locators (DOI or stable landing page); it does not collapse records merely because their titles are similar. Six same-metadata groups with different canonical resources remain explicitly unresolved rather than being silently discarded. The release keeps records with missing abstracts for metadata and citation workflows. Abstract-dependent retrieval must treat those records as missing data rather than as negative evidence. The declared scope, per-venue coverage, identity policy, and exact snapshot identity are in `profiles/security-20-v2/config.yaml` and `data/profiles/security-20-v2/manifest.json`.

## Reviewer quick start

### Linux and macOS

Requires Python 3.11 or 3.12, Git, and Bash.

```bash
git clone --branch v1.1.0 https://github.com/sidneibarbieri/topvenues-tool.git
cd topvenues-tool
bash reproduce.sh --profile security-20-v2
```

The command installs declared dependencies, verifies the snapshot manifest, materializes a disposable SQLite database, runs the regression suite, builds FTS5, exercises search, and writes a BibTeX sample. It needs no API key, institutional access, publisher credential, or GPU. After dependencies are installed, validation is offline.

### Native Windows

Requires Python 3.11 or 3.12 with the Python Launcher (`py`), Git, and
PowerShell. Use the native PowerShell workflow rather than editing the Unix
script or mixing Git Bash and PowerShell environments:

```powershell
git clone --branch v1.1.0 https://github.com/sidneibarbieri/topvenues-tool.git
cd topvenues-tool
powershell -ExecutionPolicy Bypass -File .\reproduce.ps1 -Profile security-20-v2
```

The script creates `.venv` and installs `requirements.txt` itself. If a prior
attempt created `.venv` with Python 3.10 or older, remove only that directory
before rerunning: `Remove-Item -Recurse -Force .venv`.

Do not start a second reproduction while one is running. The verification
script refreshes a disposable local SQLite copy; materialization is serialized
and a locked database produces an actionable wait-and-retry error.

For a concise evidence map, read [REVIEWER_GUIDE.md](REVIEWER_GUIDE.md). For the full artifact boundary, read [ARTIFACT_README.md](ARTIFACT_README.md).

## Use the local interface

```bash
source .venv/bin/activate
python -m streamlit run web/app.py
```

On Windows PowerShell, activate with `.\.venv\Scripts\Activate.ps1` before
running the same `python -m streamlit run web/app.py` command.

The interface exposes coverage inspection, substring and BM25-ranked search, author and trend exploration, and exports. Search and author analytics offer an explicit Security Big Four (Tier 1) scope: ACM CCS, IEEE S&P, USENIX Security, and NDSS. Insights are traceable: selecting a venue, year, or topic-trend bar opens the corresponding records, while each author view can open that author's supporting papers. Author views measure corpus visibility under a declared venue-tier heuristic; they do not measure citations, quality, seniority, or authority. See [docs/RESEARCH_WORKFLOWS.md](docs/RESEARCH_WORKFLOWS.md) before using a tier restriction in a review protocol. It runs against the local snapshot at `http://localhost:8501`.

## Inspect abstract evidence

[![Abstract-text search with populated previews](docs/assets/topvenues-abstract-search.png)](docs/assets/topvenues-abstract-search.pdf)

This capture applies the interface's **Abstract contains** filter to `intrusion detection` in the frozen `security-20` profile. Every displayed row has an abstract preview. The linked [high-resolution PDF](docs/assets/topvenues-abstract-search.pdf) preserves the capture for close inspection.

## Command-line workflows

```bash
# Inspect corpus state and coverage
python -m src.cli --profile security-20-v2 stats

# Search records that mention a term
python -m src.cli --profile security-20-v2 search --abstract "intrusion detection"

# Rank records by multi-token FTS5/BM25 relevance
python -m src.cli --profile security-20-v2 search --rank "memory corruption mitigations" --limit 20

# Export a review-ready subset
python -m src.cli --profile security-20-v2 export --format bibtex --tech "fuzzing" -o fuzzing.bib

# Build the Hugging Face Parquet export from the immutable profile
python -m src.cli --profile security-20-v2 export-hf --release-tag v1.1.0
```

Substring and ranked search answer different questions: substring search finds records that mention text, whereas ranked search orders title, abstract, and author matches by BM25. Multi-word ranked queries use token semantics.

## Scope and extension

Venue names and policies are explicit because they define the scientific denominator. Adding a venue requires a deliberate configuration change, normalization mapping, coverage check, a new immutable profile snapshot, and a new release tag. It is not a routine refresh of this object.

Live `download`, `consolidate`, `extract`, and `bibtex` commands are maintenance operations. They may use changing external services; they do not alter the committed release snapshot. Unexpected collection errors surface to the caller rather than being silently converted into successful enrichment.

The released profile disables live refresh controls in the web interface. The controlled successor-profile procedure is in [docs/PROFILE_REFRESH.md](docs/PROFILE_REFRESH.md); the SBSeg bench and seven-minute presentation walkthrough is in [docs/SBSEG_2026_DEMO_SCRIPT.md](docs/SBSEG_2026_DEMO_SCRIPT.md).

The companion full paper's 200-record manual audit and live baseline comparison are documented in [docs/COMPANION_FULL_PAPER_EVALUATION.md](docs/COMPANION_FULL_PAPER_EVALUATION.md). They remain explicitly bound to that paper's frozen snapshot and are not reused as a v2 accuracy claim.

## Hugging Face export

The public dataset is at [sidneibarbieri/topvenues](https://huggingface.co/datasets/sidneibarbieri/topvenues). The dataset card records the selected profile, source tag, and snapshot SHA-256.

## License and provenance

TopVenues code is released under the MIT license. DBLP bibliographic metadata and BibTeX follow DBLP's CC0 terms. Original abstract text remains subject to its source terms; the tool records provenance and does not claim ownership of third-party abstracts.
