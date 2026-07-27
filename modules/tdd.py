"""tdd — test-driven development.

Write the failing test first, then the code that passes it. Binds whenever the
agent modifies code; conforms only if a failing test for that task was recorded
*before* the change. Deterministic tier: it reads the trace, so the check is
exact and free.
"""

from __future__ import annotations

from openharness.checks import earlier_in_task, on_event
from openharness.events import Event, EventType
from openharness.module import (CheckOutcome, CheckTier, HarnessModule, Price,
                                 Severity, Upstream)


def _check(event: Event, history: list[Event]) -> CheckOutcome:
    test = earlier_in_task(history, EventType.TEST_WRITTEN, EventType.TEST_RUN)
    if test is None:
        return CheckOutcome.failed(
            "code changed with no failing test written first",
            severity=Severity.MINOR)
    if test.get("status") == "failing" or test.type == EventType.TEST_WRITTEN:
        return CheckOutcome.passed(
            "failing test preceded the code change",
            evidence=f"ts={test.ts} {test.type}")
    return CheckOutcome.failed(
        "a test ran first, but it was already passing — not test-driven",
        severity=Severity.MINOR)


MODULE = HarnessModule(
    id="tdd",
    name="Test-Driven Development",
    summary="Red before green: a failing test must precede the code that passes it.",
    scope=on_event(EventType.CODE_MODIFIED),
    check=_check,
    price=Price.for_tier(CheckTier.DETERMINISTIC),
    upstream=Upstream(repo="openharness/modules-tdd", version="1.2.0"),
    tags=("workflow", "quality"),
)
