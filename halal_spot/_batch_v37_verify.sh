set -u
cd /home/user/TRADING-BOT/halal_spot
PY=/home/user/.venv_v37/bin/python
say(){ echo "=== $1 $(date +%H:%M:%S) ==="; }
say "W2";     $PY -u lab_v36_live_readiness.py run S1_COIN_GUARD_BOS --window W2
say "OLD7";   $PY -u lab_v36_live_readiness.py run S1_COIN_GUARD_BOS --window OLD7
say "FULL15"; $PY -u lab_v36_live_readiness.py run S1_COIN_GUARD_BOS --window FULL15
say "MODERN"; $PY -u lab_v36_live_readiness.py run S1_COIN_GUARD_BOS --window MODERN
echo VERIFY_V37_DONE
