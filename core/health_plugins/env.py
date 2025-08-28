from __future__ import annotations
import os
from . import register

WANTED = [
    "NOISE_SEEK_BEACON_PATH",
    "NOISE_SEEK_SUBSCRIPTIONS_PATH",
    "TARGET_STREAM_ID",
    "LISTENER_ID",
    "RUNTIME_DIR",
]


@register("env:variables", order=20)
def check(report):
    present = []
    missing = []
    for key in WANTED:
        if key in os.environ and os.environ[key]:
            present.append(key)
        else:
            missing.append(key)
    if missing:
        report.add(
            "env:variables",
            "WARN",
            f"present={len(present)} missing={','.join(missing)}",
        )
    else:
        report.add("env:variables", "OK", f"{len(present)} vars")
