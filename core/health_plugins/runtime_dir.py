from __future__ import annotations
import os
from pathlib import Path
import tempfile
from . import register


@register("runtime_dir_writable", order=30)
def check(report):
    runtime_dir = Path(os.getenv("RUNTIME_DIR", "runtime"))
    try:
        runtime_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        report.add("runtime_dir_writable", "FAIL", f"mkdir error: {e}", fatal=True)
        return
    try:
        with tempfile.NamedTemporaryFile(dir=runtime_dir, delete=True):
            pass
    except Exception as e:
        report.add(
            "runtime_dir_writable",
            "FAIL",
            f"cannot write temp file: {e}",
            fatal=True,
        )
        return
    report.add("runtime_dir_writable", "OK", str(runtime_dir))
