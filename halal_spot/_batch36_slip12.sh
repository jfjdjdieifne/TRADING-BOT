set -e
cd /home/user/TRADING-BOT/halal_spot
say(){ echo "=== $1 $(date +%H:%M:%S) ==="; }
for a in EXIT_SLIP_1BPS EXIT_SLIP_2BPS; do
  say "$a W1"; python3 -u lab_v36_live_readiness.py run $a --window W1
  say "$a W2"; python3 -u lab_v36_live_readiness.py run $a --window W2
done
echo SLIP12_DONE
