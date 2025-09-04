from __future__ import annotations
import json
import os
from pathlib import Path
from . import register


@register("subscriptions_file", order=70)
def check(report):
    path = Path(os.getenv("NOISE_SEEK_SUBSCRIPTIONS_PATH", "runtime/subscriptions.json"))
    if not path.exists():
        report.add("subscriptions_file", "WARN", "missing")
        return
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as e:
        report.add("subscriptions_file", "FAIL", f"parse error: {e}")
        return
    if not isinstance(data, dict):
        report.add("subscriptions_file", "FAIL", "root not object")
        return
    report.add("subscriptions_file", "OK", f"streams={len(data)}")
