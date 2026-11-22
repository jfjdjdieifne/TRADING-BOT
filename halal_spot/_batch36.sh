set -e
cd /home/user/TRADING-BOT/halal_spot
say(){ echo "=== $1 $(date +%H:%M:%S) ==="; }
# ---------- TASK 1: the champion + the PURE stack ----------
say "S1_COIN_GUARD_BOS W2";  python3 -u lab_v36_live_readiness.py run S1_COIN_GUARD_BOS --window W2
say "S1_BOS_PLUS_FLASH W1";   python3 -u lab_v36_live_readiness.py run S1_BOS_PLUS_FLASH --window W1
say "S1_BOS_PLUS_FLASH W2";   python3 -u lab_v36_live_readiness.py run S1_BOS_PLUS_FLASH --window W2
# ---------- TASK 2: exit slippage ladder ----------
for a in EXIT_SLIP_3BPS EXIT_SLIP_5BPS EXIT_SLIP_8BPS BOTH_SLIP_5BPS; do
  say "$a W1"; python3 -u lab_v36_live_readiness.py run $a --window W1
  say "$a W2"; python3 -u lab_v36_live_readiness.py run $a --window W2
done
echo TASK12_DONE
