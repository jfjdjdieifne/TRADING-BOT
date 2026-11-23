set -e
cd /home/user/TRADING-BOT/halal_spot
say(){ echo "=== $1 $(date +%H:%M:%S) ==="; }
say "FULL15"; python3 -u lab_v36_live_readiness.py run S1_COIN_GUARD_BOS --window FULL15
say "OLD7";   python3 -u lab_v36_live_readiness.py run S1_COIN_GUARD_BOS --window OLD7
say "MODERN"; python3 -u lab_v36_live_readiness.py run S1_COIN_GUARD_BOS --window MODERN
echo OOS_DONE
