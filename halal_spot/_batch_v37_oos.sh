set -u
cd /home/user/TRADING-BOT/halal_spot
PY=/home/user/.venv_v37/bin/python
say(){ echo "=== $1 $(date +%H:%M:%S) ==="; }
say "B0 OLD7";   $PY -u lab_v37_anti_fragile.py run B0 --window OLD7
say "B0 FULL15"; $PY -u lab_v37_anti_fragile.py run B0 --window FULL15
say "B0 MODERN"; $PY -u lab_v37_anti_fragile.py run B0 --window MODERN_24M
echo OOS_V37_DONE
