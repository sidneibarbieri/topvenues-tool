# Data layout

`data/profiles/security-20/` is the immutable data object for this release. It contains the compressed SQLite snapshot and `manifest.json`, which declares its SHA-256, counts, venue-level coverage, and observed years.

`data/dataset/papers.db.gz` is a convenience copy used by the local web and CLI defaults. It represents the same `security-20` corpus. The manifested profile snapshot is authoritative for reproduction.

`data/awards/` contains source-backed optional award annotations. They enrich exploration output and do not change corpus inclusion, coverage, or ranking claims.

Generated databases, caches, downloaded DBLP dumps, and live-enrichment workspaces are intentionally excluded from the release.
