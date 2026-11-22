set -e
cd /home/user/TRADING-BOT/halal_spot
MONTHS="2023-08 2023-09 2023-10 2023-11 2023-12 2024-01 2024-02 2024-03 2024-04 2024-05 2024-06 2024-07 2024-08 2024-09 2024-10"
SYMS="BTCUSDT ETHUSDT SOLUSDT BNBUSDT XRPUSDT AVAXUSDT LINKUSDT ADAUSDT"
echo "[1] extract official BTC/ETH 5m ZIPs"
rm -rf /tmp/vfx && mkdir -p /tmp/vfx
for s in BTCUSDT ETHUSDT; do for m in $MONTHS; do
  tar xzf /tmp/vf.tgz -C /tmp/vfx --strip-components=3 "volatility-forecasting-main/data/raw/$s/$s-5m-$m.zip"
done; done
ls /tmp/vfx | wc -l
echo "[2] fetcher (official ZIPs -> .csv.gz)"
python3 fetch_binance_5m.py --from-zips /tmp/vfx --symbols BTCUSDT ETHUSDT --months $MONTHS
echo "[3] keep the official conversions as validation references"
for s in BTCUSDT ETHUSDT; do for m in $MONTHS; do
  cp -f data/binance_5m/${s}_5m/${m}.csv.gz data/binance_5m/${s}_5m/${m}.csv.gz.ref
done; done
ls data/binance_5m/*/*.csv.gz.ref | wc -l
echo "[4] sparse-clone the eight 1m repositories"
rm -rf /tmp/k1m && mkdir -p /tmp/k1m
for s in $SYMS; do
  git clone -q --depth 1 --filter=blob:none --sparse "https://github.com/parshant231234-eng/${s}-Historical-Data.git" "/tmp/k1m/$s"
  cd "/tmp/k1m/$s"
  pats=""
  for m in $MONTHS; do y=${m%-*}; mo=${m#*-}; pats="$pats /1m/$y/$mo"; done
  git sparse-checkout set --no-cone $pats
  cd /home/user/TRADING-BOT/halal_spot
  echo "   $s: $(find /tmp/k1m/$s/1m -name '*.csv' | wc -l) csv"
done
echo "[5] rebuild all eight symbols 1m -> 5m, validated against the official refs"
python3 build_5m_from_1m.py --src /tmp/k1m --symbols $SYMS --months $MONTHS --validate
echo "[6] inventory"
ls data/binance_5m/*/*.csv.gz | wc -l
python3 - <<'PY'
import json,pathlib
r=json.loads(pathlib.Path('data/binance_5m/BUILD_5M_REPORT.json').read_text())
print("missing:",r["missing"])
chk=[x for x in r["rows"] if x.get("reference")]
print("validated months:",len(chk),"common bars:",sum(x["common_rows"] for x in chk),
      "all OHLC exact:",all(x.get("OHLC_exact") for x in chk))
PY
echo DONE_REBUILD
