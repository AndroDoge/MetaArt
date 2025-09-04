# Rooms (English Overview)

Protector of the art and users of it.

![CI](https://github.com/AndroDoge/rooms/actions/workflows/ci.yml/badge.svg)
<!-- Future: Coverage badge (e.g. Codecov) -->

This repository includes a seeking / beacon subsystem producing:
- `beacons.jsonl` (JSONL log of seeking state transitions)
- `subscriptions.json` (active subscription intents)

Diagnostics tool:
```
python -m core.health            # human table
python -m core.health --json     # machine JSON
python -m core.health --list-checks
```

Health output columns:
- check name (ordered by declared numeric order; lower order runs earlier)
- status (OK | WARN | FAIL)
- elapsed_ms (execution time in ms, one decimal)
- detail (contextual info)

Plugin checks (initial set):
- `python_version`
- `env:variables`
- `runtime_dir_writable`
- `beacons_file`
- `beacons_parse`
- `beacon_shape`
- `subscriptions_file`
- `target_stream`
- `import:core.beacon_writer`

Add new check: create `core/health_plugins/<name>.py` with `@register("your_check_name", order=NN)`.

(Planned) Threshold customization: we can add either CLI flags or env vars (e.g. `HEALTH_BEACONS_OK_RATIO`, `HEALTH_BEACONS_WARN_RATIO`) if dynamic tuning is needed. Let us know preferred interface.

Quick smoke:
```
python scripts/smoke_beacons.py
python -m core.health
```

Audio / Show Assets:
- Generative audio scripts under `scripts/audio/`
- Show runner: `scripts/show/run_show.py --config docs/show_config.example.yaml`
- Detailed plan: `docs/SHOW_PLAN.md`

Static artifact:
- `artifacts/welcome.html?status=200` -> renders JSON status object

See `docs/SEEKING.md` for beacon & subscription format details.
