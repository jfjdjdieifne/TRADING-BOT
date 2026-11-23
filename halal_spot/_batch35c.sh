set -e
cd /home/user/TRADING-BOT/halal_spot
echo "=== S1_FLASH_SELLER W1 $(date +%H:%M:%S) ==="
python3 -u lab_v35_surgical_shield.py run S1_FLASH_SELLER --window W1
echo "=== S1_FLASH_SELLER W2 $(date +%H:%M:%S) ==="
python3 -u lab_v35_surgical_shield.py run S1_FLASH_SELLER --window W2
echo ALL_DONE
