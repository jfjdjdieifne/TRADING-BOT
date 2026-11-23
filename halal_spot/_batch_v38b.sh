set -u
cd /home/user/TRADING-BOT/halal_spot
PY=/home/user/.venv_v38/bin/python
say(){ echo "=== $1 $(date +%H:%M:%S) ==="; }
say "B0 W1 (identity re-check after wiring)"
$PY -u lab_v38_dol_harvester.py run B0 --window W1
for a in TRAIL_1H DOL_LOCK ANTI_BE_12 ANTI_BE_15 MIN_ROOM_1 ADAPT_4H; do
  say "$a W1"; $PY -u lab_v38_dol_harvester.py run $a --window W1
done
echo PHASE1_DONE
