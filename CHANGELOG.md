# Changelog

## 1.3.0 — 2026-08-24

- Publish `security-20-v3`, preserving prior snapshots while enforcing the
  declared 2019–2026 window and merging two DOI aliases confirmed by Crossref.
- Record all six same-metadata identity decisions in a versioned adjudication
  log; four pairs remain distinct because publisher resources remain distinct.
- Add Researcher Radar rankings by raw paper count (default) and by the
  separately labeled venue-tier heuristic, each with any/first/last-author views.
- Reproduce with a cross-platform, hash-locked dependency set on Python
  3.11–3.14.

## 1.2.1 — 2026-08-24

- Keep display preferences outside the semantic search-filter reset, removing
  a redundant Streamlit session-state assignment and its runtime warning.

## 1.2.0 — 2026-08-24

- Make declared venue tiers first-class in web search, author analytics,
  topic trends, CLI search, and exports.
- Preserve chronological order in annual charts and add selectable,
  consistently styled volume and share views.
- Reset stale search state before insight drill-downs and expose the active
  tier scope and tier evidence in result tables and author shortlists.
- Mark partial publication years to prevent incomplete-year trend claims.
- Install and health-check the web interface in the Linux/macOS and native
  Windows reviewer workflows.
- Test the artifact on Linux and Windows with Python 3.11 through 3.14 and
  refuse in-place overwrite of an immutable successor snapshot.

## 1.1.0 — 2026-08-24

- Publish `security-20-v2`, a successor snapshot that merges only records
  sharing an exact canonical DOI or landing page; the frozen `security-20`
  profile used by the SBSeg-SF paper remains available unchanged.
- Make the identity policy executable and testable, preserving distinct works
  that merely have similar titles.
- Add all-author, first-author, and last-author views to tier-aware author
  visibility.
- Add explicit insight-to-search navigation for venue and year distributions.
- Remove the stale, hard-coded test count from the web interface.

## 1.0.1 — 2026-08-18

- Add a native Windows PowerShell reproduction workflow.
- Close every core SQLite connection deterministically before temporary-file cleanup.
- Validate the reviewer workflow on Windows and Linux with Python 3.11 and 3.12 in CI.
- Align release identity, test counts, and platform instructions across reviewer documentation.

## 1.0.0 — 2026-07-25

- Publish the immutable `security-20` corpus profile and initial reviewer workflow.
