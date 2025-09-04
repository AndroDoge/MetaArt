from __future__ import annotations
from . import register


@register("import:core.beacon_writer", order=25)
def check(report):
    try:
        __import__("core.beacon_writer")
    except ModuleNotFoundError:
        report.add("import:core.beacon_writer", "WARN", "module not present")
    except Exception as e:  # pragma: no cover
        report.add("import:core.beacon_writer", "FAIL", f"error {e}")
    else:
        report.add("import:core.beacon_writer", "OK", "imported")
