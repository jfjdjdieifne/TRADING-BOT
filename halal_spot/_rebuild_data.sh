set -e
cd /home/user/TRADING-BOT/halal_spot
MONTHS="2023-08 2023-09 2023-10 2023-11 2023-12 2024-01 2024-02 2024-03 2024-04 2024-05 2024-06 2024-07 2024-08 2024-09 2024-10"
SYMS="BTCUSDT ETHUSDT SOLUSDT BNBUSDT XRPUSDT AVAXUSDT LINKUSDT ADAUSDT"
TB=/home/user/vf.tgz
echo "[0] tarball"
[ -s $TB ] || curl -sL -o $TB https://codeload.github.com/jainlakshay22/volatility-forecasting/tar.gz/refs/heads/main
ls -l $TB
echo "[1] extract official BTC/ETH 5m ZIPs"
rm -rf /home/user/vfx && mkdir -p /home/user/vfx
for s in BTCUSDT ETHUSDT; do for m in $MONTHS; do
  tar xzf $TB -C /home/user/vfx --strip-components=3 "volatility-forecasting-main/data/raw/$s/$s-5m-$m.zip"
done; done
ls /home/user/vfx | wc -l
echo "[2] fetcher"
python3 fetch_binance_5m.py --from-zips /home/user/vfx --symbols BTCUSDT ETHUSDT --months $MONTHS | tail -2
echo "[3] official conversions become the validation references"
for s in BTCUSDT ETHUSDT; do for m in $MONTHS; do
  cp -f data/binance_5m/${s}_5m/${m}.csv.gz data/binance_5m/${s}_5m/${m}.csv.gz.ref
done; done
echo "[4] sparse-clone the eight 1m repositories"
K=/home/user/k1m; rm -rf $K; mkdir -p $K
for s in $SYMS; do
  git clone -q --depth 1 --filter=blob:none --sparse "https://github.com/parshant231234-eng/${s}-Historical-Data.git" "$K/$s"
  cd "$K/$s"; pats=""
  for m in $MONTHS; do y=${m%-*}; mo=${m#*-}; pats="$pats /1m/$y/$mo"; done
  git sparse-checkout set --no-cone $pats
  cd /home/user/TRADING-BOT/halal_spot
  echo "   $s: $(find $K/$s/1m -name '*.csv' 2>/dev/null | wc -l) csv"
done
echo "[5] rebuild 1m -> 5m validated against the official refs"
python3 build_5m_from_1m.py --src $K --symbols $SYMS --months $MONTHS --validate | tail -6
echo "[6] inventory"
ls data/binance_5m/*/*.csv.gz | wc -l
echo DONE_REBUILD
