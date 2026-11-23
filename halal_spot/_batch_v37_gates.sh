set -u
cd /home/user/TRADING-BOT/halal_spot
PY=/home/user/.venv_v37/bin/python
say(){ echo "=== $1 $(date +%H:%M:%S) ==="; }
for a in GATE_4H GATE_1H GATE_BOTH CD_1H FIXBE; do
  for w in W1 W2 OLD7 MOD_Y2; do
    say "$a $w"; $PY -u lab_v37_anti_fragile.py run $a --window $w || echo "FAIL $a $w"
  done
done
say "B0 W2 (needed for the comparison table)"; $PY -u lab_v37_anti_fragile.py run B0 --window W2
echo MATRIX_GATES_DONE
