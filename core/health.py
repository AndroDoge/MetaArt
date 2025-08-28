#!/usr/bin/env python3
"""
Lightweight health diagnostics for the seeking/beacon subsystem.

Checks performed (all non-fatal unless marked *):
  1. Python version (>=3.11 recommended)
  2. Environment variables presence (optional vs required)
  3. Runtime directory writability *
  4. Beacon file readability & line parse ratio
  5. Subscriptions file readability & JSON shape
  6. Recent beacons structural sanity (fields: state, stream_id)
  7. Optional: TARGET_STREAM_ID referenced by at least one seeking_* beacon (informational)

Exit code:
  0 if no fatal errors
  1 if a fatal error (writability or hard parse failure) occurred
"""

from __future__ import annotations
import os
import sys
import json
from pathlib import Path
from typing import Any, List, Dict

try:
    from core import beacon_writer  # type: ignore
except Exception as e:
    beacon_writer = None  # type: ignore
    _import_error = e
else:
    _import_error = None

BEACON_PATH = os.getenv("NOISE_SEEK_BEACON_PATH", "runtime/beacons.jsonl")
SUBSCRIPTIONS_PATH = os.getenv("NOISE_SEEK_SUBSCRIPTIONS_PATH", "runtime/subscriptions.json")
RUNTIME_DIR = str(Path(BEACON_PATH).parent)

RECOMMENDED_PY = (3, 11)


class HealthReport:
    def __init__(self):
        self.items: List[Dict[str, Any]] = []
        self.fatal = False

    def add(self, name: str, status: str, detail: str = "", fatal: bool = False):
        self.items.append({"check": name, "status": status, "detail": detail})
        if fatal and status != "OK":
            self.fatal = True

    def render(self) -> str:
        lines = []
        width = max((len(i["check"]) for i in self.items), default=4) + 2
        for i in self.items:
            lines.append(f"{i['check']:<{width}} {i['status']:>6}  {i['detail']}")
        return "\n".join(lines)


def check_python(report: HealthReport):
    cur = sys.version_info[:3]
    if cur < RECOMMENDED_PY:
        report.add("python_version", "WARN", f"running {cur}, recommended >= {RECOMMENDED_PY}")
    else:
        report.add("python_version", "OK", f"{cur}")


def check_env(report: HealthReport):
    interesting = [
        "NOISE_SEEK_BEACON_PATH",
        "NOISE_SEEK_SUBSCRIPTIONS_PATH",
        "TARGET_STREAM_ID",
        "LISTENER_ID",
    ]
    for key in interesting:
        val = os.getenv(key)
        if val:
            report.add(f"env:{key}", "OK", val)
        else:
            report.add(f"env:{key}", "INFO", "unset")


def check_runtime_dir(report: HealthReport):
    p = Path(RUNTIME_DIR)
    try:
        p.mkdir(parents=True, exist_ok=True)
        test_file = p / ".health_write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        report.add("runtime_dir_writable", "OK", RUNTIME_DIR, fatal=True)
    except Exception as e:
        report.add("runtime_dir_writable", "FAIL", f"{RUNTIME_DIR}: {e}", fatal=True)


def parse_beacons(report: HealthReport) -> List[Dict[str, Any]]:
    path = Path(BEACON_PATH)
    if not path.exists():
        report.add("beacons_file", "INFO", "absent (no beacons yet)")
        return []
    if beacon_writer and hasattr(beacon_writer, "read_recent"):
        try:
            data = beacon_writer.read_recent(str(path), max_lines=500)
            if isinstance(data, list):
                report.add("beacons_file", "OK", f"{len(data)} entries (via beacon_writer)")
                return data
            else:
                report.add("beacons_file", "WARN", "unexpected type from beacon_writer")
        except Exception as e:
            report.add("beacons_file", "WARN", f"read via beacon_writer failed: {e}")

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    parsed: List[Dict[str, Any]] = []
    bad = 0
    for ln in lines[-500:]:
        try:
            obj = json.loads(ln)
            if isinstance(obj, dict):
                parsed.append(obj)
        except Exception:
            bad += 1
    total = len(lines[-500:])
    ratio = (bad / total) if total else 0.0
    status = "OK" if ratio < 0.05 else "WARN"
    detail = f"{len(parsed)} parsed / {total} lines, bad={bad}"
    report.add("beacons_parse", status, detail)
    return parsed


def check_subscriptions(report: HealthReport):
    path = Path(SUBSCRIPTIONS_PATH)
    if not path.exists():
        report.add("subscriptions_file", "INFO", "absent (no subscriptions yet)")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            keys = len(data)
            report.add("subscriptions_file", "OK", f"{keys} stream keys")
        else:
            report.add("subscriptions_file", "WARN", "not a JSON object")
    except Exception as e:
        report.add("subscriptions_file", "WARN", f"parse error: {e}")


def check_beacon_shape(report: HealthReport, beacons: List[Dict[str, Any]]):
    if not beacons:
        return
    missing = 0
    for b in beacons[-50:]:
        if "state" not in b or "stream_id" not in b:
            missing += 1
    if missing == 0:
        report.add("beacon_shape", "OK", "last 50 have state+stream_id")
    else:
        report.add("beacon_shape", "WARN", f"{missing} / {min(50, len(beacons))} missing fields")


def check_target_presence(report: HealthReport, beacons: List[Dict[str, Any]]):
    target = os.getenv("TARGET_STREAM_ID")
    if not target:
        return
    found = any(b.get("stream_id") == target and str(b.get("state", "")).startswith("seeking_") for b in beacons[-200:])
    if found:
        report.add("target_stream", "OK", f"seeking beacon seen for {target}")
    else:
        report.add("target_stream", "INFO", f"no seeking beacon yet for {target}")


def check_import(report: HealthReport):
    if _import_error:
        report.add("import:core.beacon_writer", "INFO", f"not imported: {_import_error}")
    else:
        report.add("import:core.beacon_writer", "OK", "loaded")


def main():
    report = HealthReport()
    check_python(report)
    check_env(report)
    check_import(report)
    check_runtime_dir(report)
    beacons = parse_beacons(report)
    check_subscriptions(report)
    check_beacon_shape(report, beacons)
    check_target_presence(report, beacons)

    print(report.render())
    if report.fatal:
        sys.exit(1)


if __name__ == "__main__":
    main()