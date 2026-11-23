set -u
cd /home/user/TRADING-BOT/halal_spot
PY=/home/user/.venv_v38/bin/python
say(){ echo "=== $1 $(date +%H:%M:%S) ==="; }
# W1 first for every arm (cheapest, and the identity window)
for a in TRAIL_1H TRAIL_1H_1PCT TRAIL_1H_30M DOL_LOCK ANTI_BE_12 ANTI_BE_15 MIN_ROOM_1 ADAPT_4H TRAIL_DOL; do
  say "$a W1"; $PY -u lab_v38_dol_harvester.py run $a --window W1
done
echo V38_W1_DONE
