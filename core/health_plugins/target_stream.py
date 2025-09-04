from __future__ import annotations
import json
import os
from pathlib import Path
from collections import deque
from . import register


@register("target_stream", order=80)
def check(report):
    target = os.getenv("TARGET_STREAM_ID")
    if not target:
        report.add("target_stream", "WARN", "TARGET_STREAM_ID unset")
        return
    path = Path(os.getenv("NOISE_SEEK_BEACON_PATH", "runtime/beacons.jsonl"))
    if not path.exists():
        report.add("target_stream", "WARN", "no beacons file")
        return
    found = False
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in deque(f, maxlen=400):
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if (
                    isinstance(obj, dict)
                    and obj.get("stream_id") == target
                    and str(obj.get("state", "")).startswith("seeking_")
                ): 
                    found = True
                    break
    except Exception as e:
        report.add("target_stream", "FAIL", f"read error: {e}")
        return
    if found:
        report.add("target_stream", "OK", target)
    else:
        report.add("target_stream", "WARN", f"no seeking beacon for {target}")
