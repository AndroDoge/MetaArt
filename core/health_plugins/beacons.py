from __future__ import annotations
import json
import os
from pathlib import Path
from collections import deque
from . import register

MAX_READ = 500


@register("beacons_file", order=40)
def file_check(report):
    path = Path(os.getenv("NOISE_SEEK_BEACON_PATH", "runtime/beacons.jsonl"))
    if not path.exists():
        report.add("beacons_file", "WARN", f"missing {path}")
        return
    if not path.is_file():
        report.add("beacons_file", "FAIL", f"not a file: {path}", fatal=False)
        return
    try:
        size = path.stat().st_size
        report.add("beacons_file", "OK", f"{size} bytes")
    except Exception as e:  # pragma: no cover
        report.add("beacons_file", "FAIL", f"stat error: {e}", fatal=False)


@register("beacons_parse", order=50)
def parse_check(report):
    path = Path(os.getenv("NOISE_SEEK_BEACON_PATH", "runtime/beacons.jsonl"))
    if not path.exists():
        report.add("beacons_parse", "WARN", "no file")
        return
    good = 0
    bad = 0
    lines_kept = deque(maxlen=MAX_READ)
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                lines_kept.append(line.rstrip("\n"))
    except Exception as e:
        report.add("beacons_parse", "FAIL", f"read error: {e}")
        return
    last_struct_ok = 0
    for ln in lines_kept:
        if not ln.strip():
            continue
        try:
            obj = json.loads(ln)
            if isinstance(obj, dict):
                good += 1
                if "stream_id" in obj and "state" in obj:
                    last_struct_ok += 1
            else:
                bad += 1
        except Exception:
            bad += 1
    total = good + bad
    if total == 0:
        report.add("beacons_parse", "WARN", "empty")
        return
    ratio = good / total
    status = "OK" if ratio > 0.95 else ("WARN" if ratio > 0.7 else "FAIL")
    report.add(
        "beacons_parse",
        status,
        f"good={good} bad={bad} ratio={ratio:.2%} structural={last_struct_ok}",
    )


@register("beacon_shape", order=60)
def shape_check(report):
    path = Path(os.getenv("NOISE_SEEK_BEACON_PATH", "runtime/beacons.jsonl"))
    if not path.exists():
        report.add("beacon_shape", "WARN", "no file")
        return
    structural = 0
    scanned = 0
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in deque(f, maxlen=50):
                scanned += 1
                try:
                    obj = json.loads(line)
                    if (
                        isinstance(obj, dict)
                        and "state" in obj
                        and "stream_id" in obj
                    ):
                        structural += 1
                except Exception:
                    pass
    except Exception as e:
        report.add("beacon_shape", "FAIL", f"read error: {e}")
        return
    if scanned == 0:
        report.add("beacon_shape", "WARN", "no lines")
        return
    pct = structural / scanned
    status = "OK" if pct > 0.9 else "WARN"
    report.add("beacon_shape", status, f"{structural}/{scanned} ({pct:.0%})")
