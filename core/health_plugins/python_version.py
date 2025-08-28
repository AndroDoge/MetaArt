from __future__ import annotations
import sys
from . import register

RECOMMENDED = (3, 11)


@register("python_version", order=10)
def check(report):
    cur = sys.version_info[:3]
    if cur < RECOMMENDED:
        report.add(
            "python_version",
            "WARN",
            f"running {cur[0]}.{cur[1]}.{cur[2]}, recommended >= {RECOMMENDED[0]}.{RECOMMENDED[1]}",
        )
    else:
        report.add("python_version", "OK", f"{cur[0]}.{cur[1]}.{cur[2]}")
