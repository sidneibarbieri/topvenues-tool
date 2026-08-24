# Changelog

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
