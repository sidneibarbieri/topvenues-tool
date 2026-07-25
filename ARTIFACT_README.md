# TopVenues Research Artifact

TopVenues materializes a declared cybersecurity-literature scope as a local, versioned SQLite corpus. This release packages the `security-20` profile.

## Artifact identity

| Property | Value |
| --- | --- |
| Release tag | `sbseg2026-sf-submission-r1` |
| Profile | `security-20` |
| Records | 20,305 |
| Abstract-enriched records | 17,491 |
| BibTeX entries | 20,305 |
| Automated tests | 238 |
| Snapshot gzip SHA-256 | `5a35bd6e3ec6845a0fde4cc3d6aa05b1db04e511cb39e783eeaee2cea7493b08` |

## Public reviewer path

```bash
bash reproduce.sh
```

This is the authoritative zero-cost validation path. It verifies the manifest, materializes the snapshot, runs the test suite, exercises search, and produces a sample export. It does not call live scholarly APIs or reproduce results from another paper.

## Structure

| Path | Purpose |
| --- | --- |
| `src/` | Python implementation of collection, normalization, search, exports, and profiles |
| `web/` | Local Streamlit interface |
| `tests/` | Automated regression and integrity tests |
| `scripts/verify_profile_snapshot.py` | Manifest and checksum verifier |
| `scripts/benchmark_search.py` | Host-local search exercise |
| `profiles/security-20/config.yaml` | Declared venue and year scope |
| `data/profiles/security-20/` | Immutable snapshot and manifest |
| `data/awards/` | Source-backed optional award annotations |

## Reproducibility boundary

The committed snapshot is the evidence object. Future DBLP downloads or abstract enrichment may create a new snapshot, but cannot silently modify this release. Benchmark timings are machine-dependent diagnostics, not scientific performance claims. The artifact records missing abstracts instead of deleting records or inferring their content.

## License and data terms

The code is MIT licensed. DBLP metadata and BibTeX follow DBLP's CC0 terms. Abstract text is retained with provenance for research indexing and remains subject to the terms of its original sources.
