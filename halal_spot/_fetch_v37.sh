#!/bin/bash
# v37 data rebuild: GitHub 1m repos -> /home/user/k1m/<SYM>/1m/<Y>/<M>/
set -u
SYMS="BTCUSDT ETHUSDT SOLUSDT BNBUSDT XRPUSDT AVAXUSDT LINKUSDT ADAUSDT"
PATS=""
for y in 2023 2024 2025 2026; do
  for m in 01 02 03 04 05 06 07 08 09 10 11 12; do PATS="$PATS /1m/$y/$m"; done
done
mkdir -p /home/user/k1m
for s in $SYMS; do
  echo "=== $s $(date +%H:%M:%S) ==="
  if [ ! -d /home/user/k1m/$s/.git ]; then
    git clone --filter=blob:none --sparse --depth 1 \
      https://github.com/parshant231234-eng/$s-Historical-Data /home/user/k1m/$s || { echo "CLONE_FAIL $s"; continue; }
  fi
  cd /home/user/k1m/$s
  rm -f .git/index.lock
  git sparse-checkout set --no-cone $PATS || { echo "SPARSE_FAIL $s"; continue; }
  n=$(find 1m -name '*.csv' 2>/dev/null | wc -l)
  echo "    $s csv=$n du=$(du -sh 1m 2>/dev/null | cut -f1)"
  cd /home/user/TRADING-BOT/halal_spot
done
echo FETCH_V37_DONE
