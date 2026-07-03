#!/usr/bin/env bash
set -Eeuo pipefail

# Run pilot.py for tickers in config/default.yaml that are not yet listed in
# reextract_tickers. Output is streamed to the terminal and saved under log/.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_PATH="$PROJECT_ROOT/config/default.yaml"
LOG_DIR="$PROJECT_ROOT/log/pilot_missing_reextract"
SUMMARY_LOG="$LOG_DIR/run_all.log"
FAILED_LOG="$LOG_DIR/failed_tickers.txt"

mkdir -p "$LOG_DIR"
: > "$SUMMARY_LOG"
: > "$FAILED_LOG"

cd "$PROJECT_ROOT"

if [[ "${SKIP_CONDA:-0}" != "1" && "${CONDA_DEFAULT_ENV:-}" != "senior_project" ]]; then
  if command -v conda >/dev/null 2>&1; then
    eval "$(conda shell.bash hook)"
    conda activate senior_project
  else
    echo "[warn] conda not found; continuing with current Python environment" | tee -a "$SUMMARY_LOG"
  fi
fi

mapfile -t TICKERS < <(
  python - "$CONFIG_PATH" <<'PY'
from pathlib import Path
import sys

import yaml

cfg = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8")) or {}
tickers = {str(t).upper() for t in cfg.get("tickers", []) if t}
reextract = {str(t).upper() for t in cfg.get("reextract_tickers", []) if t}

for ticker in sorted(tickers - reextract):
    print(ticker)
PY
)

{
  echo "============================================================"
  echo "Pilot missing reextract run"
  echo "Config: $CONFIG_PATH"
  echo "Log dir: $LOG_DIR"
  echo "Extra pilot args: ${*:-<none>}"
  echo "Missing tickers: ${TICKERS[*]:-<none>}"
  echo "============================================================"
} | tee -a "$SUMMARY_LOG"

if [[ "${#TICKERS[@]}" -eq 0 ]]; then
  echo "[done] No missing tickers. config.tickers is already covered by reextract_tickers." | tee -a "$SUMMARY_LOG"
  exit 0
fi

for ticker in "${TICKERS[@]}"; do
  ticker_lower="$(printf '%s' "$ticker" | tr '[:upper:]' '[:lower:]')"
  ticker_log="$LOG_DIR/${ticker_lower}_pilot.log"
  : > "$ticker_log"

  {
    echo
    echo "============================================================"
    echo "Starting pilot for $ticker"
    echo "Ticker log: $ticker_log"
    echo "============================================================"
  } | tee -a "$SUMMARY_LOG" "$ticker_log"

  if python scripts/pilot.py --ticker "$ticker" --sync-reextract "$@" 2>&1 | tee -a "$ticker_log" "$SUMMARY_LOG"; then
    echo "[ok] $ticker pilot completed" | tee -a "$SUMMARY_LOG" "$ticker_log"
  else
    status=$?
    echo "$ticker" >> "$FAILED_LOG"
    echo "[fail] $ticker pilot failed with exit code $status" | tee -a "$SUMMARY_LOG" "$ticker_log"
  fi
done

if [[ -s "$FAILED_LOG" ]]; then
  echo "[done] Some pilots failed. See $FAILED_LOG and per-ticker logs in $LOG_DIR" | tee -a "$SUMMARY_LOG"
  exit 1
fi

echo "[done] All missing pilot runs completed successfully." | tee -a "$SUMMARY_LOG"
