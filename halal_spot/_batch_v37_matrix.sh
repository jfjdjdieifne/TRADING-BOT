set -u
cd /home/user/TRADING-BOT/halal_spot
PY=/home/user/.venv_v37/bin/python
say(){ echo "=== $1 $(date +%H:%M:%S) ==="; }
say "B0 W1 identity check"; $PY -u lab_v37_anti_fragile.py run B0 --window W1
for a in RATCHET_2R RATCHET_3R RATCHET_3RT RATCHET_LAD_A RATCHET_LAD_B; do
  for w in W2 OLD7 MOD_Y2; do
    say "$a $w"; $PY -u lab_v37_anti_fragile.py run $a --window $w || echo "FAIL $a $w"
  done
done
echo MATRIX_RATCHET_DONE
