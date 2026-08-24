# Data layout

`data/profiles/security-20/` is the frozen data object for the accepted SBSeg-SF paper. `security-20-v2` is its exact-resource deduplicated successor. `security-20-v3` is the current strict-window, identity-adjudicated release. Each profile contains a compressed SQLite snapshot and `manifest.json`, which declares its SHA-256, counts, venue-level coverage, and observed years.

`data/dataset/papers.db.gz` is retained only for the frozen artifact lineage. The local web and CLI default to `security-20-v3`; manifested profile snapshots are authoritative for reproduction. `data/adjudication/` records evidence-backed identity decisions rather than hiding them in implementation code.

`data/awards/` contains source-backed optional award annotations. They enrich exploration output and do not change corpus inclusion, coverage, or ranking claims.

Generated databases, caches, downloaded DBLP dumps, and live-enrichment workspaces are intentionally excluded from the release.
