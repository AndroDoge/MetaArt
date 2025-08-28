"""
Seeking / Self-Seeking state machine skeleton.

Responsible for:
- Tracking produced & delivered ticks
- Determining seeking state transitions
- Deciding when to emit a beacon dict (caller persists via beacon_writer)
"""

from __future__ import annotations
import os
import time
import enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


class SeekingState(str, enum.Enum):
    IDLE = "idle"
    SEEKING_LOW = "seeking_low"
    SEEKING_ESCALATE = "seeking_escalate"
    ATTACHED = "attached"
    SHUTDOWN = "shutdown"      # placeholder / not used in MVP
    COMMONS = "commons"        # placeholder / not used in MVP


@dataclass
class SeekingConfig:
    lonely_after_s: float = float(os.getenv("NOISE_SEEK_LONELY_AFTER_S", 12))
    escalate_after_s: float = float(os.getenv("NOISE_SEEK_ESCALATE_AFTER_S", 30))
    shutdown_after_s: float = float(os.getenv("NOISE_SEEK_SHUTDOWN_AFTER_S", 120))

    beacon_interval_low_s: float = float(os.getenv("NOISE_SEEK_BEACON_INTERVAL_LOW_S", 10))
    beacon_interval_escalate_s: float = float(os.getenv("NOISE_SEEK_BEACON_INTERVAL_ESC_S", 5))

    beacon_path: str = os.getenv("NOISE_SEEK_BEACON_PATH", "runtime/beacons.jsonl")
    subscriptions_path: str = os.getenv("NOISE_SEEK_SUBSCRIPTIONS_PATH", "runtime/subscriptions.json")

    stream_id: str = os.getenv("NOISE_STREAM_ID", "noise_metadata")
    mode: str = os.getenv("NOISE_MODE", "markov")

    # Optional hints (may be filled by caller)
    tempo_range_s: tuple[float, float] = (float(os.getenv("NOISE_MIN_INTERVAL_S", 1.0)),
                                          float(os.getenv("NOISE_MAX_INTERVAL_S", 4.0)))


@dataclass
class SeekingStateData:
    state: SeekingState = SeekingState.IDLE
    produced_ticks: int = 0
    delivered_ticks: int = 0

    first_lonely_ts: Optional[float] = None
    last_beacon_ts: Optional[float] = None
    beacon_count: int = 0
    attached: bool = False

    # Cached ratios
    loneliness_ratio: float = 0.0


class SeekingController:
    def __init__(self, cfg: SeekingConfig):
        self.cfg = cfg
        self.data = SeekingStateData()

    # --- External interface -------------------------------------------------

    def record_tick(self):
        self.data.produced_ticks += 1

    def record_delivery(self, delivered_n: int = 1):
        """Increment delivered count (call when a listener actually consumes).
        MVP: might not be called yet => delivered stays at 0."""
        self.data.delivered_ticks += delivered_n

    def update_and_maybe_beacon(self, now: Optional[float] = None,
                                entropy_profile: Optional[str] = None,
                                tokens_hint: Optional[list[str]] = None,
                                spore: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update state machine; if conditions satisfied -> return beacon dict.
        Caller is responsible for persisting the beacon via beacon_writer.
        """
        now = now or time.time()

        self._refresh_subscriptions(now)
        self._update_loneliness(now)
        self._transition(now)

        if self.data.state in (SeekingState.SEEKING_LOW, SeekingState.SEEKING_ESCALATE):
            if self._should_emit_beacon(now):
                return self._build_beacon(now,
                                          entropy_profile=entropy_profile,
                                          tokens_hint=tokens_hint,
                                          spore=spore)
        return None

    def is_attached(self) -> bool:
        return self.data.state == SeekingState.ATTACHED

    # --- Internal logic -----------------------------------------------------

    def _refresh_subscriptions(self, now: float):
        """Load subscription file; if stream_id present with non-empty list -> attached."""
        path = self.cfg.subscriptions_path
        try:
            if os.path.exists(path):
                import json
                with open(path, "r", encoding="utf-8") as f:
                    subs = json.load(f)
                listeners = subs.get(self.cfg.stream_id, [])
                if listeners:
                    if not self.data.attached:
                        # Transition to attached
                        self.data.attached = True
                        self.data.state = SeekingState.ATTACHED
                        # Reset loneliness timer
                        self.data.first_lonely_ts = None
        except Exception as e:
            # Non-fatal; log-friendly stub
            print(f"[seeking] subscription refresh error: {e}")

    def _update_loneliness(self, now: float):
        prod = self.data.produced_ticks
        delv = self.data.delivered_ticks
        if prod <= 0:
            self.data.loneliness_ratio = 0.0
        else:
            if delv >= prod:
                self.data.loneliness_ratio = 0.0
            else:
                # Simplistic ratio
                self.data.loneliness_ratio = (prod - delv) / prod

        if not self.data.attached:
            if self.data.first_lonely_ts is None:
                self.data.first_lonely_ts = now
        else:
            self.data.first_lonely_ts = None

    def _transition(self, now: float):
        if self.data.attached:
            # Once attached, remain until further logic (not defined in MVP)
            return

        if self.data.first_lonely_ts is None:
            self.data.state = SeekingState.IDLE
            return

        duration = now - self.data.first_lonely_ts
        if duration >= self.cfg.shutdown_after_s:
            # MVP: remain in escalate; future: set SHUTDOWN or COMMONS
            self.data.state = SeekingState.SEEKING_ESCALATE
        elif duration >= self.cfg.escalate_after_s:
            self.data.state = SeekingState.SEEKING_ESCALATE
        elif duration >= self.cfg.lonely_after_s:
            self.data.state = SeekingState.SEEKING_LOW
        else:
            self.data.state = SeekingState.IDLE

    def _should_emit_beacon(self, now: float) -> bool:
        interval = (self.cfg.beacon_interval_low_s
                    if self.data.state == SeekingState.SEEKING_LOW
                    else self.cfg.beacon_interval_escalate_s)
        last = self.data.last_beacon_ts or 0.0
        return (now - last) >= interval

    def _build_beacon(self, now: float,
                      entropy_profile: Optional[str],
                      tokens_hint: Optional[list[str]],
                      spore: Optional[str]) -> Dict[str, Any]:
        self.data.last_beacon_ts = now
        self.data.beacon_count += 1

        beacon = {
            "ts": _iso_ts(now),
            "stream_id": self.cfg.stream_id,
            "state": self.data.state.value,
            "seq": self.data.produced_ticks,
            "produced_ticks": self.data.produced_ticks,
            "delivered_ticks": self.data.delivered_ticks,
            "loneliness_ratio": round(self.data.loneliness_ratio, 5),
            "mode": self.cfg.mode,
            "entropy_profile": entropy_profile or "unknown",
            "tempo_range_s": list(self.cfg.tempo_range_s),
            "tokens_hint": tokens_hint or [],
            "spore": spore or "",
            "beacon_n": self.data.beacon_count
        }
        return beacon


def _iso_ts(t: float) -> str:
    import datetime
    return datetime.datetime.utcfromtimestamp(t).isoformat(timespec="milliseconds") + "Z"