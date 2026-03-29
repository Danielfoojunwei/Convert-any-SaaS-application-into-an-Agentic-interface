#!/usr/bin/env bash
set -u

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <pass_id>" >&2
  exit 2
fi

PASS_ID="$1"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT/verification_logs/pass_${PASS_ID}"
SUMMARY="$LOG_DIR/summary.tsv"
mkdir -p "$LOG_DIR"

cd "$ROOT" || exit 1

echo -e "scenario\ttest_target\texit_code" > "$SUMMARY"

run_scenario() {
  local scenario="$1"
  local target="$2"
  local logfile="$LOG_DIR/${scenario}.log"

  echo "===== ${scenario} :: ${target} =====" | tee "$logfile"
  pytest -q "$target" 2>&1 | tee -a "$logfile"
  local status=${PIPESTATUS[0]}
  echo -e "${scenario}\t${target}\t${status}" >> "$SUMMARY"
  return 0
}

run_scenario "S1" "tests/test_full_pipeline.py"
run_scenario "S2" "tests/test_sprint2.py"
run_scenario "S3" "tests/test_sprint3_5.py"
run_scenario "S4" "tests/test_e2e.py"
run_scenario "S5" "tests/test_launch_integration.py"
run_scenario "S6" "tests/test_plugin_integration.py"

echo
cat "$SUMMARY"
