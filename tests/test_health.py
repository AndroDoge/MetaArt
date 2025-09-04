"""
Tests for core.health module.
"""
import json
import subprocess
import sys
from pathlib import Path

MODULE = "core.health"

def run_health(*args):
    return subprocess.run([sys.executable, "-m", MODULE, *args], capture_output=True, text=True)

def test_health_text_mode_runs():
    proc = run_health()
    # Allow exit 0 or 1 (fatal only if runtime dir unwritable); treat other codes as failure
    assert proc.returncode in (0, 1), proc.stderr
    out = proc.stdout
    assert "python_version" in out
    assert "runtime_dir_writable" in out

def test_health_json_mode_structure(tmp_path, monkeypatch=None):  # monkeypatch is pytest fixture if available
    # Point beacon + subscription paths to temp so test is deterministic
    beacon_path = tmp_path / "beacons.jsonl"
    subs_path = tmp_path / "subscriptions.json"
    env = {
        **dict(os.environ),
        "NOISE_SEEK_BEACON_PATH": str(beacon_path),
        "NOISE_SEEK_SUBSCRIPTIONS_PATH": str(subs_path),
    }
    # Pre-create a couple of beacon lines
    beacon_path.write_text('{"stream_id":"alpha","state":"seeking_init"}\n' '{"stream_id":"alpha","state":"seeking_active"}\n', encoding="utf-8")
    proc = subprocess.run([sys.executable, "-m", MODULE, "--json"], capture_output=True, text=True, env=env)
    assert proc.returncode in (0, 1), proc.stderr
    try:
        data = json.loads(proc.stdout)
    except Exception as e:  # pragma: no cover
        raise AssertionError(f"Not JSON output: {e}\nSTDOUT=\n{proc.stdout}")
    assert isinstance(data, list)
    keys = {item.get("check") for item in data if isinstance(item, dict)}
    assert "python_version" in keys
    assert "beacons_parse" in keys
