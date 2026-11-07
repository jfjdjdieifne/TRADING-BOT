"""Atomic, fail-closed artifact writing for the CSM research runs.

SAFE INTEGRATION V1 (audit F §"Output failure and reproduction artifacts"):
a serialization failure must NEVER leave a truncated artifact, and a run
must never write into a directory that already holds target artifacts
(seed/stale files would be mistaken for this run's outputs).

Smallest necessary OPEN local mechanism — no framework: temp-file + fsync +
``os.replace`` per target, all temps staged first, residue cleaned on any
failure.  Nothing here touches CLOSED modules or market-data contracts.
"""
from __future__ import annotations

import gzip
import json
import os
from pathlib import Path
from typing import Dict, Iterable, Optional


class ArtifactWriteError(RuntimeError):
    """Raised when a target artifact cannot be written completely."""


def require_clean_out_dir(out_dir: Path, target_names: Iterable[str]) -> None:
    """Fail closed unless every target name is absent in ``out_dir``.

    Stale/seeded artifacts next to a failed write are indistinguishable from
    fresh outputs — the run refuses to mix them (audit F: "left a truncated
    gzip alongside seeded, stale record/manifest files").
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    clashes = [n for n in target_names if (out_dir / n).exists()]
    if clashes:
        raise ArtifactWriteError(
            f"output directory {out_dir} already contains target "
            f"artifacts {clashes}; refusing to mix stale/seeded files with "
            "this run's outputs (use a clean output directory)")


def atomic_write_text(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` atomically (temp + fsync + replace)."""
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        if tmp.exists():
            tmp.unlink()
        raise


def atomic_write_json(path: Path, obj: object) -> None:
    atomic_write_text(path, json.dumps(obj, indent=1, default=str))


def atomic_write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    """Atomic JSONL (one JSON object per line)."""
    text = "".join(json.dumps(r, default=str) + "\n" for r in rows)
    atomic_write_text(path, text)


def atomic_write_jsonl_gzip(path: Path, rows: Iterable[dict]) -> None:
    """Atomic gzip-JSONL: serialize COMPLETELY to a temp file first — a
    serialization failure leaves no target and no truncated gzip."""
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    try:
        with gzip.open(tmp, "wt", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, default=str) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        if tmp.exists():
            tmp.unlink()
        raise


def write_run_artifacts(out_dir: Path,
                        artifacts: Dict[str, object]) -> Dict[str, str]:
    """Write every named artifact atomically into a CLEAN ``out_dir``.

    ``artifacts`` maps target filename -> payload:
      * ``str``            -> text
      * ``dict``/``list``  -> JSON (indent=1)
      * ("jsonl", rows)    -> JSONL
      * ("jsonl.gz", rows) -> gzip JSONL

    All temps are staged BEFORE any target is replaced; a failure removes
    every staged temp and leaves no target partially written.  Returns
    ``{name: sha256-hex}`` of the written files.
    """
    import hashlib

    out_dir = Path(out_dir)
    require_clean_out_dir(out_dir, artifacts.keys())
    staged: Dict[str, Path] = {}
    try:
        for name, payload in artifacts.items():
            tmp = out_dir / (name + ".tmp")
            if isinstance(payload, str):
                data = payload.encode("utf-8")
                tmp.write_bytes(data)
            elif isinstance(payload, tuple) and payload and \
                    payload[0] == "jsonl":
                text = "".join(json.dumps(r, default=str) + "\n"
                               for r in payload[1])
                tmp.write_bytes(text.encode("utf-8"))
            elif isinstance(payload, tuple) and payload and \
                    payload[0] == "jsonl.gz":
                with gzip.open(tmp, "wt", encoding="utf-8") as fh:
                    for r in payload[1]:
                        fh.write(json.dumps(r, default=str) + "\n")
            else:
                tmp.write_bytes(
                    json.dumps(payload, indent=1, default=str).encode("utf-8"))
            with open(tmp, "rb") as fh:
                os.fsync(fh.fileno())
            staged[name] = tmp
        # every payload serialized successfully -> commit (atomic replace)
        hashes: Dict[str, str] = {}
        for name, tmp in staged.items():
            target = out_dir / name
            os.replace(tmp, target)
            hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
        return hashes
    except BaseException:
        for tmp in staged.values():
            if tmp.exists():
                tmp.unlink()
        raise
