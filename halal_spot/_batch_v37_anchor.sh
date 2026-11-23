set -u
cd /home/user/TRADING-BOT/halal_spot
PY=/home/user/.venv_v37/bin/python
say(){ echo "=== $1 $(date +%H:%M:%S) ==="; }
say "B0 MOD_Y2"; $PY -u lab_v37_anti_fragile.py run B0 --window MOD_Y2
say "B0 MOD_Y1"; $PY -u lab_v37_anti_fragile.py run B0 --window MOD_Y1
say "RATCHET_2R W1"; $PY -u lab_v37_anti_fragile.py run RATCHET_2R --window W1
echo ANCHOR_DONE
