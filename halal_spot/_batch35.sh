set -e
cd /home/user/TRADING-BOT/halal_spot
for arm in S1_COIN_GUARD S1_COIN_GUARD_K3_14d S1_COIN_GUARD_BOS S1_WIDE_CAP S1_TOUCH_GUARD S1_SURGICAL_COMBO S1_SURGICAL_COMBO_DUST; do
  for w in W1 W2; do
    echo "=== $arm $w $(date +%H:%M:%S) ==="
    python3 -u lab_v35_surgical_shield.py run $arm --window $w
  done
done
# the identity arm's missing W2
echo "=== BASE_S1_TEL_3R W2 $(date +%H:%M:%S) ==="
python3 -u lab_v35_surgical_shield.py run BASE_S1_TEL_3R --window W2
echo ALL_DONE
