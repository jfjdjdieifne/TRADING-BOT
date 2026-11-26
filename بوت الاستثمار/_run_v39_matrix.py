"""Runner: the v39 STEP 2 matrix, strictly ONE sequential process.

Ordering is deliberate. The arms the STEP 1 audit scored positive run across
ALL FIVE windows first, because cross-window consistency is the only thing
that can ship. The arms it scored negative run W1-only and are labelled as
such in the report -- a W1-only result is not evidence, and pretending
otherwise is exactly the overfitting the project forbids.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import lab_v39_golden_sniper as L

TIER1 = ["AGE12", "SNIPER", "DEMAND4H", "TSTOP2H"]   # all five windows
TIER2 = ["AGE24", "DEMAND1H", "FVG_TRAIL", "TSTOP4H", "TSTOP12H"]  # W1 only

def main() -> None:
    for arm in TIER1:
        for w in L.FIVE:
            if (L.RESULTS / f"lab_v39_{arm}_{w}.json").exists():
                print(f"skip {arm}/{w} (done)", flush=True)
                continue
            L.drive(arm, w)
    for arm in TIER2:
        if (L.RESULTS / f"lab_v39_{arm}_W1.json").exists():
            print(f"skip {arm}/W1 (done)", flush=True)
            continue
        L.drive(arm, "W1")
    L.table()
    print("\n### MATRIX COMPLETE ###", flush=True)

if __name__ == "__main__":
    main()
