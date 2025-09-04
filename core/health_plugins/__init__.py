from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Tuple
import time

@dataclass
class HealthItem:
    check: str
    status: str  # OK|WARN|FAIL
    detail: str = ""
    elapsed_ms: float | None = None

@dataclass
class HealthReport:
    items: List[HealthItem] = field(default_factory=list)
    fatal: bool = False

    def add(
        self,
        name: str,
        status: str,
        detail: str = "",
        *,
        fatal: bool = False,
        elapsed_ms: float | None = None,
    ) -> None:
        self.items.append(HealthItem(name, status, detail, elapsed_ms))
        if fatal and status == "FAIL":
            self.fatal = True

    @property
    def has_warn(self) -> bool:
        return any(i.status == "WARN" for i in self.items)

    def render(self) -> str:
        width = max((len(i.check) for i in self.items), default=4) + 2
        ms_width = 8
        lines = []
        for i in self.items:
            ms = f"{i.elapsed_ms:.1f}ms" if i.elapsed_ms is not None else ""
            lines.append(
                f"{i.check:<{width}} {i.status:>5}  {ms:>{ms_width}}  {i.detail}"
            )
        return "\n".join(lines)

    def to_json(self) -> list[dict[str, Any]]:
        return [
            {
                "check": i.check,
                "status": i.status,
                "detail": i.detail,
                "elapsed_ms": i.elapsed_ms,
            }
            for i in self.items
        ]

# Internal registry entries: (order, name, fn)
REGISTRY: List[Tuple[int, str, Callable[[HealthReport], Any]]] = []

def register(name: str, *, order: int = 100):
    """
    Decorator to register a health check.

    order: smaller runs earlier. Non-unique is fine; stable sort keeps definition order
    within identical order values.
    """

    def dec(fn: Callable[[HealthReport], Any]):
        REGISTRY.append((order, name, fn))
        return fn

    return dec

# Import plugin modules (side effect: registration)
from . import python_version  # noqa: E402,F401
from . import env  # noqa: E402,F401
from . import import_bw  # noqa: E402,F401
from . import runtime_dir  # noqa: E402,F401
from . import beacons  # noqa: E402,F401
from . import subscriptions  # noqa: E402,F401
from . import target_stream  # noqa: E402,F401

def run_all() -> HealthReport:
    report = HealthReport()
    for order, name, fn in sorted(REGISTRY, key=lambda t: t[0]):
        start = time.perf_counter()
        try:
            fn(report)
        except Exception as e:  # pragma: no cover - defensive
            elapsed = (time.perf_counter() - start) * 1000
            report.add(name, "FAIL", f"exception: {e}", fatal=False, elapsed_ms=elapsed)
        else:
            if not report.items or report.items[-1].check != name:
                elapsed = (time.perf_counter() - start) * 1000
                report.add(name, "OK", "no detail", elapsed_ms=elapsed)
            else:
                elapsed = (time.perf_counter() - start) * 1000
                report.items[-1].elapsed_ms = elapsed
    return report
