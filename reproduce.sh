#!/usr/bin/env bash
# Reproduce the artifact's headline claims in a single shot.
#
# What this script verifies:
#   1. Installation succeeds with declared dependencies.
#   2. Database snapshot bootstraps to the expected counts.
#   3. Test suite passes (no failures).
#   4. A representative keyword search returns within the latency budget.
#   5. A BibTeX export produces a non-empty .bib file.
#   6. The early-signal study reproduces the headline preprint rate.
#   7. The scientific-readiness study and baselines reproduce the headline
#      lift/recall and control comparisons.
#
# Exit code 0 → all claims hold; non-zero → first failure is reported.

set -euo pipefail

cd "$(dirname "$0")"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$PWD/.cache/uv}"

EXPECTED_PAPERS=144785
EXPECTED_ABSTRACTS=17603
EXPECTED_BIBTEX=144785

step() { printf "\n\033[1;34m▶ %s\033[0m\n" "$*"; }
ok()   { printf "  \033[32m✓\033[0m %s\n" "$*"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$*"; exit 1; }

# ── 1. Python and dependencies ────────────────────────────────────────────
step "Checking Python and dependencies"
if [[ -n "${PYTHON:-}" ]]; then
  python_bin="$PYTHON"
else
  python_bin=""
  for candidate in python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      python_bin="$candidate"
      break
    fi
  done
fi
if [[ -z "$python_bin" ]] || ! command -v "$python_bin" >/dev/null 2>&1; then
  fail "Python 3.11+ is required (set PYTHON=… to override)"
fi
ok "bootstrap interpreter: $($python_bin --version)"
"$python_bin" - <<'PY' || fail "Python 3.11 or newer is required"
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY

if [[ ! -d .venv ]]; then
  step "Creating .venv"
  if command -v uv >/dev/null 2>&1; then
    uv venv --quiet --seed --python "$python_bin" .venv
  else
    "$python_bin" -m venv .venv
  fi
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python - <<'PY' || fail "active virtual environment must use Python 3.11 or newer"
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
ok "active environment: $(python --version)"
if command -v uv >/dev/null 2>&1; then
  uv pip install --quiet -r requirements.txt
else
  PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 pip install --quiet --prefer-binary --timeout 60 -r requirements.txt
fi
ok "dependencies installed"

# ── 2. Bootstrap from the gzipped snapshot ────────────────────────────────
step "Bootstrapping the database from papers.db.gz"
rm -f data/dataset/papers.db data/dataset/papers.db.sync-id
stats=$(python -m src.cli stats)
echo "$stats" | sed 's/^/  /'

papers=$(echo "$stats"     | awk '/Total Papers:/ {print $NF}')
abstracts=$(echo "$stats"  | awk '/With Abstracts:/ {print $3}')
bibtex=$(echo "$stats"     | awk '/With BibTeX:/ {print $3}')

[[ "$papers"    == "$EXPECTED_PAPERS"    ]] || fail "expected $EXPECTED_PAPERS papers, got $papers"
[[ "$abstracts" == "$EXPECTED_ABSTRACTS" ]] || fail "expected $EXPECTED_ABSTRACTS abstracts, got $abstracts"
[[ "$bibtex"    == "$EXPECTED_BIBTEX"    ]] || fail "expected $EXPECTED_BIBTEX BibTeX entries, got $bibtex"
ok "database state matches headline claims"

# Snapshot identity: reviewers can confirm they hold the same release.
snapshot_sha=$(shasum -a 256 data/dataset/papers.db.gz | awk '{print $1}')
expected_snapshot_sha=$(awk '{print $1}' data/dataset/papers.db.gz.sha256)
[[ "$snapshot_sha" == "$expected_snapshot_sha" ]] || \
  fail "snapshot SHA-256 mismatch: expected $expected_snapshot_sha, got $snapshot_sha"
ok "snapshot papers.db.gz SHA-256 verified: $snapshot_sha"

# ── 3. Test suite ─────────────────────────────────────────────────────────
step "Running test suite"
test_output=$(python -m pytest -q 2>&1 || true)
echo "$test_output" | tail -3 | sed 's/^/  /'
test_count=$(echo "$test_output" | awk '/passed/ {print $1}' | head -1)
echo "$test_output" | grep -qE "failed|error" && fail "test suite did not pass cleanly"
[[ -n "$test_count" ]] || fail "no tests ran"
ok "all $test_count tests pass"

# ── 3b. Researcher-facing analytics and award data ───────────────────────
step "Validating author analytics and award metadata"
python - <<'PY' || fail "analytics or award metadata validation failed"
from pathlib import Path
from src.analytics import reference_authors
from src.awards import build_corpus_award_map

db = Path("data/dataset/papers.db")
awards = Path("data/awards")
award_map = build_corpus_award_map(awards, db)
ranked = reference_authors(db, topic="LLM", limit=20, awards_dir=awards)
assert award_map, "no award records matched the corpus"
assert ranked, "LLM author query returned no results"
assert any(entry["top4"] > 0 for entry in ranked), "author evidence has no top-four papers"
print(f"  {len(award_map)} corpus papers carry award evidence")
print(f"  {len(ranked)} author profiles returned for topic LLM")
PY
ok "author evidence and award annotations are populated"

# ── 4. Repeated search-latency benchmark ──────────────────────────────────
step "Benchmarking substring and ranked search"
python scripts/benchmark_search.py --trials 11 || fail "search benchmark failed"
ok "both search paths return results across 11 warm-cache trials"

# ── 5. BibTeX export ──────────────────────────────────────────────────────
step "Exporting a sample BibTeX corpus"
out=$(mktemp -t topvenues_repro.XXXXXX.bib)
python -m src.cli export --title "intrusion" --format bibtex --output "$out" >/dev/null
size=$(wc -c < "$out" | tr -d ' ')
[[ "$size" -gt 1000 ]] || fail "BibTeX export was empty"
ok "BibTeX export produced $(wc -l < "$out" | tr -d ' ') lines ($size bytes)"
rm -f "$out"

# ── 6. Scientific-readiness result ────────────────────────────────────────
# ── 6. Early-signal measurement ───────────────────────────────────────────
step "Reproducing the early-signal measurement"
early_output=$(python scripts/early_signal_study.py 2>&1)
echo "$early_output" | awk '/Papers with arXiv preprint/ {print "  " $0}'
echo "$early_output" | awk '/p25/ || /^[[:space:]]+[0-9]/ {print "  " $0}' | head -2
echo "$early_output" | grep -q "Papers with arXiv preprint:  1351  (29.0%)" || fail "expected 1351 early-signal matches and 29.0% rate"
echo "$early_output" | grep -q "149.0" || fail "expected median preprint lead near 149 days"
ok "early-signal study reproduces 29.0% preprint rate and median 149-day lead"

# ── 7. Scientific-readiness result ────────────────────────────────────────
step "Reproducing the scientific-readiness filter"
readiness_output=$(python scripts/readiness_study.py 2>&1)
echo "$readiness_output" | awk '/2023  thr=0.6/ {print "  " $0}'
echo "$readiness_output" | grep -q "2023  thr=0.6" || fail "missing 2023 threshold-0.6 readiness result"
echo "$readiness_output" | grep -q "lift  16.5x" || fail "expected 16.5x readiness lift"
echo "$readiness_output" | grep -q "recall  90%" || fail "expected 90% readiness recall"
ok "readiness filter reproduces 16.5x lift at 90% recall"

step "Reproducing readiness baselines"
baseline_output=$(python scripts/readiness_baselines.py 2>&1)
echo "$baseline_output" | awk '/prior top-4|prolific|random security authors|first author|senior/ {print "  " $0}'
echo "$baseline_output" | grep -q "prior top-4 (any author)     16.0%      90%  16.5x" || fail "expected prior-top-4 baseline row"
echo "$baseline_output" | grep -q "prolific (>= 3 papers)" || fail "expected prolific-author control"
echo "$baseline_output" | grep -q "random security authors" || fail "expected random-author control"
ok "readiness controls reproduce the reported baseline comparisons"

step "All headline claims reproduced"
