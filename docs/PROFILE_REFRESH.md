# Controlled profile refresh

The published `security-20-v3` snapshot is read-only. The web interface can
explore it, but it must not be used to refresh it from live APIs.

To publish a successor, an operator works in a separate profile and records:

1. the venue and year declaration;
2. source versions and collection time;
3. the exact-resource deduplication report;
4. per-venue abstract coverage and provenance;
5. automated test and search/export results; and
6. the gzip and SQLite SHA-256 values in a new manifest.

Only after those checks pass should the new snapshot receive a new semantic
release tag and replace the default researcher-facing profile. Never overwrite
an existing release snapshot or reinterpret its published counts.

The historical `scripts/build_deduplicated_profile.py` builder refuses to run
when its target already exists. It is not a refresh command. A maintainer must
first declare a new profile identifier, target directory, configuration, and
manifest, then review the resulting snapshot as a new scientific object.

The current exact-resource policy merges records only when a canonical DOI or
stable landing page is identical. Similar titles, journal extensions, and
records with different canonical resources remain distinct until they are
manually adjudicated.
