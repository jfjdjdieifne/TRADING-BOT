"""Shared deterministic helpers for read-only diagnostics."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Sequence

from trading_system.ict_engine.liquidity import LiquidityPool
from trading_system.ict_engine.order_blocks import OrderBlockDirection
from trading_system.ict_engine.swings import SwingSide

def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: str | Path, value: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, destination)


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> int:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    count = 0
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(
                json.dumps(
                    row,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
            )
            handle.write("\n")
            count += 1
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, destination)
    return count


def quantile(values: Sequence[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def distribution(values: Sequence[float]) -> dict[str, float | int | None]:
    return {
        "count": len(values),
        "minimum": min(values) if values else None,
        "q25": quantile(values, 0.25),
        "median": quantile(values, 0.5),
        "q75": quantile(values, 0.75),
        "maximum": max(values) if values else None,
    }


def ahead_pools(
    pools: Sequence[LiquidityPool], direction: OrderBlockDirection, entry: float
) -> tuple[LiquidityPool, ...]:
    wanted = SwingSide.HIGH if direction is OrderBlockDirection.BULLISH else SwingSide.LOW
    return tuple(
        pool
        for pool in pools
        if pool.side is wanted
        and ((wanted is SwingSide.HIGH and entry < pool.level) or (wanted is SwingSide.LOW and entry > pool.level))
    )


def pool_distance(pool: LiquidityPool, direction: OrderBlockDirection, entry: float) -> float:
    return pool.level - entry if direction is OrderBlockDirection.BULLISH else entry - pool.level


def iso(value) -> str | None:
    return value.isoformat() if value is not None else None
