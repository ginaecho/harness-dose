"""Small, reusable building blocks for writing module scopes and checks.

Modules are free to write raw functions, but most conformance logic is one of a
handful of shapes: "an event of type X happened earlier in this task", "this
string matches / avoids a pattern", "an LLM judge scored it". These helpers keep
the shipped modules terse and make the check *tier* explicit at the call site.
"""

from __future__ import annotations

import re
from typing import Callable, Iterable

from .events import Event
from .module import Binding, CheckOutcome, Severity, Verdict


# -- scope helpers ------------------------------------------------------------

def on_event(*types: str) -> Callable[[Event], Binding]:
    """Bind whenever the event is one of ``types``."""
    typeset = set(types)

    def scope(ev: Event) -> Binding:
        if ev.type in typeset:
            return Binding.yes(f"event.type == {ev.type!r}")
        return Binding.no()

    return scope


def on_event_when(type: str, predicate: Callable[[Event], bool],
                  because: str) -> Callable[[Event], Binding]:
    """Bind on ``type`` only when ``predicate`` also holds (e.g. payload touches PII)."""

    def scope(ev: Event) -> Binding:
        if ev.type == type and predicate(ev):
            return Binding.yes(f"{ev.type!r} and {because}")
        return Binding.no()

    return scope


# -- check helpers ------------------------------------------------------------

def earlier_in_task(history: list[Event], *types: str) -> Event | None:
    """Return the last event of any of ``types`` that preceded the current one."""
    typeset = set(types)
    # history includes the current event as its last element; skip it
    for ev in reversed(history[:-1]):
        if ev.type in typeset:
            return ev
    return None


def require_precedes(history: list[Event], *, requirement: str, requirement_types: Iterable[str],
                     pass_msg: str, fail_msg: str,
                     severity: Severity = Severity.MINOR) -> CheckOutcome:
    """Deterministic: the current event is only OK if a required event came first."""
    prior = earlier_in_task(history, *requirement_types)
    if prior is not None:
        return CheckOutcome.passed(pass_msg, evidence=f"ts={prior.ts} {prior.type}")
    return CheckOutcome.failed(fail_msg, severity=severity)


def match_ok(text: str, pattern: str, *, pass_msg: str, fail_msg: str,
             severity: Severity = Severity.MINOR) -> CheckOutcome:
    """Static: pass iff ``text`` matches ``pattern``."""
    if re.search(pattern, text or "", re.IGNORECASE | re.MULTILINE):
        return CheckOutcome.passed(pass_msg, evidence=f"matched /{pattern}/")
    return CheckOutcome.failed(fail_msg, severity=severity)


def forbid(text: str, patterns: dict[str, str], *, ok_msg: str,
           severity: Severity = Severity.CRITICAL) -> CheckOutcome:
    """Static: fail if ``text`` matches any forbidden pattern (label -> regex)."""
    hits = [label for label, pat in patterns.items()
            if re.search(pat, text or "", re.IGNORECASE)]
    if hits:
        return CheckOutcome.failed(
            f"forbidden content: {', '.join(hits)}",
            evidence=f"matched {hits}", severity=severity,
        )
    return CheckOutcome.passed(ok_msg)


def judge(score: float, *, threshold: float, rationale: str,
          severity: Severity = Severity.MINOR) -> CheckOutcome:
    """LLM-judge tier: a scored, non-deterministic verdict with a rationale.

    The score is supplied by the module (in the shipped demo it is deterministic
    so runs are reproducible; in production it would be a model call). The point
    is that this verdict carries a *price* and a *stated accuracy*, unlike the
    tiers above.
    """
    if score >= threshold:
        return CheckOutcome.passed(f"judge {score:.0f} ≥ {threshold:.0f}: {rationale}")
    return CheckOutcome.failed(
        f"judge {score:.0f} < {threshold:.0f}: {rationale}", severity=severity)
