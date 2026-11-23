set -u
cd /home/user/TRADING-BOT/halal_spot
PY=/home/user/.venv_v38/bin/python
for a in ADAPT_4H ANTI_BE_12; do
  for w in W2 MOD_Y1 MOD_Y2; do
    echo "=== $a $w $(date +%H:%M:%S) ==="
    $PY -u lab_v38_dol_harvester.py run $a --window $w
  done
done
echo PHASE2_DONE
