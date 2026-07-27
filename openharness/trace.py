"""The observable output of the layer: a stream of verdicts.

Because a module has boundaries, its activity is loggable. Every time an event
arrives and a module binds, we emit one :class:`Observation` — event → module
bound (with evidence) → verdict (with evidence and price). Collected, these are
the raw material every harness card is computed from.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from .module import Severity, Verdict


@dataclass(frozen=True)
class Observation:
    """One row of the verdict stream. This is the atom of observability."""

    ts: int
    session_id: str
    task_id: str
    task_type: str
    event_type: str
    module_id: str
    binding_evidence: str
    verdict: Verdict
    severity: Severity
    tokens: int
    tier: str
    message: str = ""
    check_evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        d["severity"] = self.severity.value
        return d

    def render_line(self) -> str:
        glyph = {
            Verdict.PASS: "✓",
            Verdict.FAIL: "✗",
            Verdict.ERROR: "⚠",
            Verdict.NOT_APPLICABLE: "·",
        }[self.verdict]
        tail = f"  — {self.message}" if self.message else ""
        return (f"[{self.ts:>3}] {self.event_type:<16} → {self.module_id:<20} "
                f"{glyph} {self.verdict.value:<4} ({self.severity.value}){tail}")


@dataclass
class Trace:
    """All observations for a single session, kept in arrival order."""

    session_id: str
    observations: list[Observation] = field(default_factory=list)

    def add(self, obs: Observation) -> None:
        self.observations.append(obs)

    def for_module(self, module_id: str) -> list[Observation]:
        return [o for o in self.observations if o.module_id == module_id]

    def __iter__(self) -> Iterable[Observation]:
        return iter(self.observations)

    def __len__(self) -> int:
        return len(self.observations)
