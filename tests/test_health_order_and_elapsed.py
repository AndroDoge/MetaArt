import json
import os
import subprocess
import sys

MODULE = "core.health"

def test_elapsed_and_order(tmp_path):
    b = tmp_path / "b.jsonl"
    b.write_text('{"stream_id":"x","state":"seeking_init"}\n', encoding="utf-8")
    subs = tmp_path / "subscriptions.json"
    subs.write_text("{}", encoding="utf-8")
    env = {
        "NOISE_SEEK_BEACON_PATH": str(b),
        "NOISE_SEEK_SUBSCRIPTIONS_PATH": str(subs),
        "RUNTIME_DIR": str(tmp_path / "rt"),
    }
    proc = subprocess.run(
        [sys.executable, "-m", MODULE, "--json"],
        capture_output=True,
        text=True,
        env={**os.environ, **env},
    )
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    for item in data:
        assert "elapsed_ms" in item
        if item["elapsed_ms"] is not None:
            assert item["elapsed_ms"] >= 0
    checks = [d["check"] for d in data]
    assert checks[0] == "python_version"
