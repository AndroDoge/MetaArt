"""
Beacon writing utility.

Responsibilities:
- Append JSON line beacons safely (best‑effort)
- (Optional) read recent tail for inspection (used by listener_sim)
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Iterable, List, Dict, Any
from collections import deque


def ensure_parent(path: str | os.PathLike):
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def append_beacon(beacon: Dict[str, Any], path: str):
    """
    Append a single beacon as JSON line.
    Minimal error handling; failures just print and return.
    """
    try:
        p = ensure_parent(path)
        line = json.dumps(beacon, separators=(",", ":"), ensure_ascii=False)
        with open(p, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"[beacon_writer] append error: {e}")


def read_recent(path: str, max_lines: int = 200) -> List[Dict[str, Any]]:
    """
    Return up to last max_lines beacons (newest last).
    If file absent -> [].
    """
    p = Path(path)
    if not p.exists():
        return []
    dq: deque[str] = deque(maxlen=max_lines)
    try:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    dq.append(line.rstrip("\n"))
    except Exception as e:
        print(f"[beacon_writer] read error: {e}")
        return []
    out: List[Dict[str, Any]] = []
    for raw in dq:
        try:
            out.append(json.loads(raw))
        except Exception:
            continue
    return out

__all__ = ["append_beacon", "read_recent", "ensure_parent"]