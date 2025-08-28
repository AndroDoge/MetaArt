"""MARKDOWN
# Rooms (English Overview)

This repository includes a seeking/beacon subsystem producing a JSONL `beacons.jsonl` log and optional `subscriptions.json` describing current stream subscription intents.

Key helper:
- `core/health.py` — diagnostics (`--json` for machine output).

Quick start:
```
python -m core.health
python -m core.health --json | jq
```

See `docs/SEEKING.md` for detailed format docs.

Smoke demo:
```
python scripts/smoke_beacons.py
python -m core.health
```
"""