"""Minimal Binance market-data + order client (stdlib + websockets).

No ccxt dependency. REST uses urllib (synchronous, fine for a bot whose main
loop is the websocket). WS uses the `websockets` package.

Supported hosts:
  * production : https://api.binance.com   + wss://stream.binance.com:9443
  * testnet    : https://testnet.binance.vision + wss://testnet.binance.vision

Never hard-code keys. Read BINANCE_API_KEY / BINANCE_API_SECRET from the
environment. `paper_only` never signs or sends an order.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import time
import urllib.parse
import urllib.request

REST_PROD = "https://api.binance.com"
WS_PROD = "wss://stream.binance.com:9443"
REST_TEST = "https://testnet.binance.vision"
WS_TEST = "wss://testnet.binance.vision"


class BinanceClient:
    def __init__(self, testnet: bool = False, paper_only: bool = True):
        self.rest = REST_TEST if testnet else REST_PROD
        self.ws_url = WS_TEST if testnet else WS_PROD
        self.paper_only = paper_only
        self.api_key = os.environ.get("BINANCE_API_KEY", "")
        self.api_secret = os.environ.get("BINANCE_API_SECRET", "")

    # ------------------------------------------------------------------ #
    def _get(self, path: str, params: dict | None = None, signed: bool = False):
        params = dict(params or {})
        params["timestamp"] = int(time.time() * 1000)
        if signed:
            if not self.api_secret:
                raise RuntimeError("BINANCE_API_SECRET not set")
            qs = urllib.parse.urlencode(params)
            sig = hmac.new(self.api_secret.encode(), qs.encode(),
                           hashlib.sha256).hexdigest()
            qs += "&signature=" + sig
            url = f"{self.rest}{path}?{qs}"
            req = urllib.request.Request(url, headers={"X-MBX-APIKEY": self.api_key})
        else:
            url = f"{self.rest}{path}"
            if params:
                # timestamp is only required for signed endpoints
                params.pop("timestamp", None)
                if params:
                    url += "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())

    def _post(self, path: str, params: dict):
        if self.paper_only:
            raise RuntimeError("paper_only: refusing to send a real order")
        params = dict(params)
        params["timestamp"] = int(time.time() * 1000)
        qs = urllib.parse.urlencode(params)
        sig = hmac.new(self.api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
        body = (qs + "&signature=" + sig).encode()
        req = urllib.request.Request(
            f"{self.rest}{path}", data=body, method="POST",
            headers={"X-MBX-APIKEY": self.api_key,
                     "Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())

    # ------------------------------------------------------------------ #
    def klines(self, symbol: str, interval: str = "5m", limit: int = 500):
        return self._get("/api/v3/klines",
                         {"symbol": symbol, "interval": interval, "limit": limit})

    def account(self):
        return self._get("/api/v3/account", signed=True)

    def place_market_order(self, symbol: str, side: str, quantity: float,
                           quote_qty: float | None = None):
        params = {"symbol": symbol, "side": side, "type": "MARKET"}
        if quote_qty is not None:
            params["quoteOrderQty"] = f"{quote_qty:.8f}"
        else:
            params["quantity"] = f"{quantity:.8f}"
        params["newOrderRespType"] = "RESULT"
        return self._post("/api/v3/order", params)

    def place_stop_market(self, symbol: str, side: str, quantity: float,
                          stop_price: float):
        params = {"symbol": symbol, "side": side, "type": "STOP_MARKET",
                  "quantity": f"{quantity:.8f}",
                  "stopPrice": f"{stop_price:.8f}",
                  "workingType": "MARK_PRICE", "closePosition": "true"}
        return self._post("/api/v3/order", params)

    def place_take_profit(self, symbol: str, side: str, quantity: float,
                          stop_price: float):
        params = {"symbol": symbol, "side": side, "type": "TAKE_PROFIT_MARKET",
                  "quantity": f"{quantity:.8f}",
                  "stopPrice": f"{stop_price:.8f}",
                  "workingType": "MARK_PRICE", "closePosition": "true"}
        return self._post("/api/v3/order", params)

    def cancel_all(self, symbol: str):
        return self._delete("/api/v3/openOrders", {"symbol": symbol})

    def _delete(self, path: str, params: dict):
        if self.paper_only:
            raise RuntimeError("paper_only: refusing to cancel real orders")
        params = dict(params)
        params["timestamp"] = int(time.time() * 1000)
        qs = urllib.parse.urlencode(params)
        sig = hmac.new(self.api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
        url = f"{self.rest}{path}?{qs}&signature={sig}"
        req = urllib.request.Request(url, method="DELETE",
                                     headers={"X-MBX-APIKEY": self.api_key})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())


# --------------------------------------------------------------------------- #
# WebSocket
# --------------------------------------------------------------------------- #
async def stream_klines(symbol: str, interval: str, on_kline, testnet: bool = False):
    """Consume combined kline + aggTrade streams. `on_kline(bar)` on close."""
    import websockets
    base = WS_TEST if testnet else WS_PROD
    streams = f"{symbol.lower()}@kline_{interval}/{symbol.lower()}@aggTrade"
    url = f"{base}/stream?streams={streams}"
    async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
        async for msg in ws:
            data = json.loads(msg)
            payload = data.get("data", data)
            if payload.get("e") == "kline":
                k = payload["k"]
                if k.get("x"):  # closed
                    on_kline({
                        "time": pd_ts(k["t"]),
                        "open": float(k["o"]), "high": float(k["h"]),
                        "low": float(k["l"]), "close": float(k["c"]),
                        "volume": float(k["v"]),
                    })
            elif payload.get("e") == "aggTrade":
                on_aggtrade(float(payload["p"]), int(payload["T"]))


def pd_ts(ms: int):
    import pandas as pd
    return pd.Timestamp(ms, unit="ms", tz="UTC")
