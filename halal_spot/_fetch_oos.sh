set -e
cd /home/user/TRADING-BOT/halal_spot
SYMS="BTCUSDT ETHUSDT SOLUSDT BNBUSDT XRPUSDT AVAXUSDT LINKUSDT ADAUSDT"
# 2023-01..2023-07  (older than anything used in v32..v35)
OLD="2023/01 2023/02 2023/03 2023/04 2023/05 2023/06 2023/07"
# 2024-11 .. 2026-11 (modern, never touched)
NEW="2024/11 2024/12 2025/01 2025/02 2025/03 2025/04 2025/05 2025/06 2025/07 2025/08 2025/09 2025/10 2025/11 2025/12 2026/01 2026/02 2026/03 2026/04 2026/05 2026/06 2026/07 2026/08 2026/09 2026/10 2026/11"
for s in $SYMS; do
  cd /home/user/k1m/$s
  pats=""
  for m in $OLD $NEW; do pats="$pats /1m/$m"; done
  echo "--- $s : $(date +%H:%M:%S)"
  git sparse-checkout set --no-cone $pats
  n=$(find 1m -name '*.csv' 2>/dev/null | wc -l)
  echo "    $s csv=$n"
  cd /home/user/TRADING-BOT/halal_spot
done
echo FETCH_DONE
