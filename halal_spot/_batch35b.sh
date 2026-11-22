set -e
cd /home/user/TRADING-BOT/halal_spot
for arm in S1_WIDE_CAP S1_SURGICAL_COMBO; do
  for w in W1 W2; do
    echo "=== $arm $w $(date +%H:%M:%S) ==="
    python3 -u lab_v35_surgical_shield.py run $arm --window $w
  done
done
for w in W1 W2; do
  echo "=== S1_TOUCH_GUARD $w $(date +%H:%M:%S) ==="
  python3 -u lab_v35_surgical_shield.py run S1_TOUCH_GUARD --window $w
done
echo ALL_DONE
