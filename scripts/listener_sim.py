#!/usr/bin/env python3
"""
Minimal listener simulation.

Loop:
1. Load / create subscriptions.json
2. If already subscribed to target stream -> sleep
3. Tail beacons.jsonl (last N lines)
4. Find newest beacon with state starting 'seeking_' whose stream_id not in subscriptions (or empty list)
5. Append listener id, write subscriptions atomically
6. Log & sleep

Env:
  LISTENER_ID (default: auto uuid shortened)
  NOISE_SEEK_BEACON_PATH
  NOISE_SEEK_SUBSCRIPTIONS_PATH
  TARGET_STREAM_ID (optional; if unset accept first seeking beacon)

Run:
  python scripts/listener_sim.py
Press Ctrl+C to stop.
"""

from __future__ import annotations
import os
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List
from core import beacon_writer  # assumes package style import (adjust if needed)

SLEEP_S = float(os.getenv("LISTENER_POLL_INTERVAL_S", 2.5))
MAX_TAIL = int(os.getenv("LISTENER_TAIL_N", 250))

BEACON_PATH = os.getenv("NOISE_SEEK_BEACON_PATH", "runtime/beacons.jsonl")
SUBSCRIPTIONS_PATH = os.getenv("NOISE_SEEK_SUBSCRIPTIONS_PATH", "runtime/subscriptions.json")
TARGET_STREAM_ID = os.getenv("TARGET_STREAM_ID")  # if None => pick first eligible

LISTENER_ID = os.getenv("LISTENER_ID") or ("listener-" + uuid.uuid4().hex[:8])

def load_subscriptions(path: str) -> Dict[str, List[str]]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[listener_sim] load subscriptions error: {e}")
        return {}

def atomic_write_json(path: str, data: Any):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, p)

def pick_beacon(beacons: List[Dict[str, Any]], subs: Dict[str, List[str]]) -> Dict[str, Any] | None:
    # iterate reversed (newest last)
    for b in reversed(beacons):
        state = b.get("state", "")
        stream_id = b.get("stream_id")
        if not state.startswith("seeking_"):
            continue
        if TARGET_STREAM_ID and stream_id != TARGET_STREAM_ID:
            continue
        current = subs.get(stream_id, [])
        if current:
            continue
        return b
    return None

def main():
    print(f"[listener_sim] start id={LISTENER_ID} beacon_path={BEACON_PATH}")
    try:
        while True:
            subs = load_subscriptions(SUBSCRIPTIONS_PATH)

            # If targeting specific stream and already subscribed -> idle sleep
            if TARGET_STREAM_ID:
                if LISTENER_ID in subs.get(TARGET_STREAM_ID, []):
                    time.sleep(SLEEP_S)
                    continue

            beacons = beacon_writer.read_recent(BEACON_PATH, max_lines=MAX_TAIL)
            if not beacons:
                time.sleep(SLEEP_S)
                continue

            chosen = pick_beacon(beacons, subs)
            if chosen is None:
                time.sleep(SLEEP_S)
                continue

            stream_id = chosen["stream_id"]
            lst = subs.setdefault(stream_id, [])
            if LISTENER_ID not in lst:
                lst.append(LISTENER_ID)
                try:
                    atomic_write_json(SUBSCRIPTIONS_PATH, subs)
                    print(f"[listener_sim] subscribed stream={stream_id} beacon_n={chosen.get('beacon_n')} seq={chosen.get('seq')}")
                except Exception as e:
                    print(f"[listener_sim] write subscription error: {e}")
            time.sleep(SLEEP_S)
    except KeyboardInterrupt:
        print("[listener_sim] exit")

if __name__ == "__main__":
    main()