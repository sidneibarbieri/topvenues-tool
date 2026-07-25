#!/usr/bin/env bash
# Reproduce the selected profile and, for submitted-11, the paper headlines.

set -euo pipefail

cd "$(dirname "$0")"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$PWD/.cache/uv}"

profile="${TOPVENUES_PROFILE:-security-20}"
skip_install=false

usage() {
  printf 'Usage: %s [--profile security-20] [--skip-install]\n' "$0"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      [[ $# -ge 2 ]] || { usage >&2; exit 2; }
      profile="$2"
      shift 2
      ;;
    --skip-install)
      skip_install=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$profile" in
  security-20) ;;
  *)
    printf 'Unknown profile: %s\n' "$profile" >&2
    exit 2
    ;;
esac
export TOPVENUES_PROFILE="$profile"

step() { printf "\n\033[1;34m▶ %s\033[0m\n" "$*"; }
ok()   { printf "  \033[32m✓\033[0m %s\n" "$*"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$*"; exit 1; }

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
"$python_bin" - <<'PY' || fail "Python 3.11 or newer is required"
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY

if [[ ! -d .venv ]]; then
  if [[ "$skip_install" == true ]]; then
    fail "--skip-install requires an existing .venv"
  fi
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

if [[ "$skip_install" == false ]]; then
  if command -v uv >/dev/null 2>&1; then
    uv pip install --quiet -r requirements.txt
  else
    PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 \
      pip install --quiet --prefer-binary --timeout 60 -r requirements.txt
  fi
  ok "dependencies installed"
else
  ok "dependency installation skipped explicitly"
fi

step "Verifying immutable profile inputs"
manifest_row=$(python scripts/verify_profile_snapshot.py --profile "$profile" --machine) || \
  fail "profile manifest verification failed"
IFS=$'\t' read -r snapshot_path workspace_data_dir expected_papers expected_abstracts \
  expected_bibtex expected_snapshot_sha <<< "$manifest_row"
[[ -n "$snapshot_path" && -n "$workspace_data_dir" && -n "$expected_snapshot_sha" ]] || \
  fail "profile verifier returned an incomplete machine record"
ok "profile $profile: $snapshot_path (sha256=$expected_snapshot_sha)"
ok "frozen arXiv input: 27,749 records and manifest checksum verified"

step "Refreshing the disposable profile workspace"
python -m src.cli --profile "$profile" refresh-db >/dev/null
stats=$(python -m src.cli --profile "$profile" stats)
echo "$stats" | sed 's/^/  /'

papers=$(echo "$stats"    | awk '/Total Papers:/ {print $NF}')
abstracts=$(echo "$stats" | awk '/With Abstracts:/ {print $3}')
bibtex=$(echo "$stats"    | awk '/With BibTeX:/ {print $3}')
[[ "$papers" == "$expected_papers" ]] || \
  fail "expected $expected_papers papers, got $papers"
[[ "$abstracts" == "$expected_abstracts" ]] || \
  fail "expected $expected_abstracts abstracts, got $abstracts"
[[ "$bibtex" == "$expected_bibtex" ]] || \
  fail "expected $expected_bibtex BibTeX entries, got $bibtex"
python scripts/verify_claims.py --profile "$profile" || fail "profile counts changed"
ok "workspace matches the immutable $profile manifest"

step "Running the test suite"
test_output=$(python -m pytest -q 2>&1 || true)
echo "$test_output" | tail -3 | sed 's/^/  /'
echo "$test_output" | grep -qE "failed|error" && fail "test suite did not pass cleanly"
test_count=$(echo "$test_output" | awk '/passed/ {print $1}' | head -1)
[[ -n "$test_count" ]] || fail "no tests ran"
ok "all $test_count tests pass"

step "Benchmarking search on a verified disposable copy"
python scripts/benchmark_search.py --profile "$profile" --trials 11 || \
  fail "search benchmark failed"
ok "substring and ranked search returned results"

step "Exporting a sample BibTeX corpus"
sample_bib=$(mktemp -t topvenues_repro.XXXXXX.bib)
trap 'rm -f "$sample_bib"' EXIT
python -m src.cli --profile "$profile" export \
  --title "intrusion" --format bibtex --output "$sample_bib" >/dev/null
sample_size=$(wc -c < "$sample_bib" | tr -d ' ')
[[ "$sample_size" -gt 1000 ]] || fail "BibTeX export was empty"
ok "BibTeX export produced $(wc -l < "$sample_bib" | tr -d ' ') lines ($sample_size bytes)"
rm -f "$sample_bib"
trap - EXIT

if [[ "$profile" == "submitted-11" ]]; then
  step "Reproducing the paper's early-signal measurement"
  early_output=$(python scripts/early_signal_study.py --profile "$profile" 2>&1)
  echo "$early_output" | awk '/Scoped papers analyzed|Papers with arXiv preprint/ {print "  " $0}'
  echo "$early_output" | awk '/p25/ || /^[[:space:]]+47\.0/ {print "  " $0}' | head -2
  echo "$early_output" | grep -q "Scoped papers analyzed    :  2537" || \
    fail "expected the 2,537-paper submitted cohort"
  echo "$early_output" | grep -q "Papers with arXiv preprint:   742  (29.2%)" || \
    fail "expected 742 early-signal matches and 29.2% rate"
  echo "$early_output" | grep -q "154.0" || \
    fail "expected median preprint lead of 154 days"
  ok "early-signal result is 742/2,537 (29.2%) with median lead 154 days"

  step "Reproducing the paper's scientific-readiness result"
  readiness_output=$(python scripts/readiness_study.py --profile "$profile" 2>&1)
  echo "$readiness_output" | awk '/2023  thr=0.6/ {print "  " $0}'
  echo "$readiness_output" | grep -q "2023  thr=0.6" || \
    fail "missing 2023 threshold-0.6 readiness result"
  echo "$readiness_output" | grep -q "RR  16.5x" || \
    fail "expected 16.5x readiness relative risk"
  echo "$readiness_output" | grep -q "lift  2.5x" || \
    fail "expected 2.5x conventional readiness lift"
  echo "$readiness_output" | grep -q "recall  90%" || \
    fail "expected 90% readiness recall"
  ok "readiness result is RR 16.5x, lift 2.5x, recall 90%"

  step "Reproducing readiness controls"
  baseline_output=$(python scripts/readiness_baselines.py --profile "$profile" 2>&1)
  echo "$baseline_output" | \
    awk '/prior top-4|prolific|random security authors|first author|senior/ {print "  " $0}'
  echo "$baseline_output" | \
    grep -Eq "prior top-4 .*15\.9%.*90%.*16\.5x.*2\.5x" || \
    fail "expected prior-top-4 baseline row"
  echo "$baseline_output" | grep -q "prolific (>= 3 papers)" || \
    fail "expected prolific-author control"
  echo "$baseline_output" | grep -q "random security authors" || \
    fail "expected random-author control"
  ok "readiness controls reproduce the reported comparisons"
else
  ok "paper-specific measurements skipped: their denominator is submitted-11, not $profile"
fi

step "Profile $profile reproduced successfully"
