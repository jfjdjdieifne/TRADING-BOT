set -u
cd /home/user/TRADING-BOT/halal_spot
PY=/home/user/.venv_v37/bin/python
say(){ echo "=== $1 $(date +%H:%M:%S) ==="; }
for b in 1 2 3 5; do
  for a in RATCHET_2R B0; do
    say "$a slip${b}bps W1"
    $PY -u lab_v37_anti_fragile.py run $a --window W1 --slip $b 2>&1 | tail -2
  done
done
echo SLIP_DONE
