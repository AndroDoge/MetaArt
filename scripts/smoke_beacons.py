"""
#!/usr/bin/env python3
"""Generate a small demo beacon sequence for manual testing of core.health.

Usage:
  python scripts/smoke_beacons.py
  python -m core.health --json
"""
from __future__ import annotations
import json
import os
import time
from pathlib import Path

BEACON_PATH = os.getenv("NOISE_SEEK_BEACON_PATH", "runtime/beacons.jsonl")
path = Path(BEACON_PATH)
path.parent.mkdir(parents=True, exist_ok=True)

def write(obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

sid = os.getenv("TARGET_STREAM_ID", "demo_stream")
now_ms = lambda: int(time.time() * 1000)
base = now_ms()
write({"stream_id": sid, "state": "seeking_init", "ts": base})
write({"stream_id": sid, "state": "seeking_active", "ts": base + 10})
write({"stream_id": sid, "state": "seeking_satisfied", "ts": base + 20, "payload": {"count": 42}})
print(f"Wrote 3 beacon lines to {path}")
"""