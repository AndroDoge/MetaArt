#!/usr/bin/env bash
# Master orchestrator with start/stop/status commands.
# Usage: ./start.sh [start|stop|restart|status]
# Default (no arg) == start
set -euo pipefail

COMMAND="${1:-start}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"
REQ_FILE="requirements.txt"
REQ_HASH_FILE=".cache/requirements.sha256"
ENV_FILE=".env"
ENV_EXAMPLE=".env.example"
PID_DIR=".cache/pids"
mkdir -p .cache "$PID_DIR"

activation() { source "$VENV_DIR/bin/activate"; }

create_venv_if_missing() {
  if [ ! -d "$VENV_DIR" ]; then
    echo "[start] Creating virtualenv..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi
  activation
}

install_requirements_if_changed() {
  local current_hash
  current_hash="$(sha256sum "$REQ_FILE" | awk '{print $1}')"
  if [ ! -f "$REQ_HASH_FILE" ] || [ "$(cat "$REQ_HASH_FILE")" != "$current_hash" ]; then
    echo "[start] Installing / updating dependencies..."
    pip install --upgrade pip wheel
    pip install -r "$REQ_FILE"
    echo "$current_hash" > "$REQ_HASH_FILE"
  else
    echo "[start] Requirements unchanged."
  fi
}

validate_env() {
  echo "[start] Validating environment (.env)"
  activation
  python scripts/util/validate_env.py || { echo "[start] Environment validation failed"; exit 1; }
}

ensure_env_file() {
  if [ ! -f "$ENV_FILE" ]; then
    echo "[start] Missing .env -> copying from example"
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    echo "[start] IMPORTANT: Edit .env to set secure secrets."
  fi
}

start_services() {
  echo "[start] Launching services..."
  bash ops/run_all.sh &
  echo $! > "$PID_DIR/orchestrator.pid"
  echo "[start] Orchestrator PID $(cat "$PID_DIR/orchestrator.pid")"
}

stop_services() {
  echo "[stop] Stopping services..."
  if [ -f "$PID_DIR/orchestrator.pid" ]; then
    kill "$(cat "$PID_DIR/orchestrator.pid")" 2>/dev/null || true
    rm -f "$PID_DIR/orchestrator.pid"
  fi
  for f in rotate_logs deps_monitor backup_state app; do
    if [ -f ".cache/${f}.pid" ]; then
      kill "$(cat ".cache/${f}.pid")" 2>/dev/null || true
      rm -f ".cache/${f}.pid"
    fi
  done
  pkill -f "uvicorn app.main:app" 2>/dev/null || true
  echo "[stop] Done."
}

status_services() {
  echo "[status] Orchestrator: $( [ -f "$PID_DIR/orchestrator.pid" ] && echo RUNNING || echo STOPPED )"
  for f in rotate_logs deps_monitor backup_state app; do
    if [ -f ".cache/${f}.pid" ] && ps -p "$(cat .cache/${f}.pid)" >/dev/null 2>&1; then
      echo "[status] $f: RUNNING (PID $(cat .cache/${f}.pid))"
    else
      echo "[status] $f: STOPPED"
    fi
  done
}

case "$COMMAND" in
  start)
    ensure_env_file
    create_venv_if_missing
    install_requirements_if_changed
    validate_env
    start_services
    ;;
  stop)
    stop_services
    ;;
  restart)
    stop_services
    sleep 1
    ensure_env_file
    create_venv_if_missing
    install_requirements_if_changed
    validate_env
    start_services
    ;;
  status)
    status_services
    ;;
  *)
    echo "Unknown command: $COMMAND"; exit 1;
    ;;
 esac
