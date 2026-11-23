set -u
cd /home/user/TRADING-BOT/halal_spot
PY=/home/user/.venv_v37/bin/python
say(){ echo "=== $1 $(date +%H:%M:%S) ==="; }
say "RATCHET_2R MODERN_24M"; $PY -u lab_v37_anti_fragile.py run RATCHET_2R --window MODERN_24M
say "RATCHET_2R MOD_Y1";     $PY -u lab_v37_anti_fragile.py run RATCHET_2R --window MOD_Y1
say "RATCHET_2R FULL15";     $PY -u lab_v37_anti_fragile.py run RATCHET_2R --window FULL15
echo FINAL_V37_DONE
