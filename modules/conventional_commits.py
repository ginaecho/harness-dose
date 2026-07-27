"""conventional-commits — every commit message follows the spec.

Binds on commit creation; conforms if the subject matches
``type(scope?): summary`` with a known type. Static tier: a regex over the
message. Minor severity — a malformed message is a nuisance, not a breach.
"""

from __future__ import annotations

import re

from openharness.checks import on_event
from openharness.events import Event, EventType
from openharness.module import (CheckOutcome, CheckTier, HarnessModule, Price,
                                 Severity, Upstream)

_TYPES = "feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert"
_PATTERN = re.compile(rf"^({_TYPES})(\([\w./-]+\))?!?: .{{1,72}}$")


def _check(event: Event, history: list[Event]) -> CheckOutcome:
    subject = (event.get("message", "") or "").splitlines()[0] if event.get("message") else ""
    if _PATTERN.match(subject):
        return CheckOutcome.passed("conventional subject", evidence=subject)
    return CheckOutcome.failed(
        "commit subject is not a conventional commit",
        evidence=subject or "<empty>",
        severity=Severity.MINOR)


MODULE = HarnessModule(
    id="conventional-commits",
    name="Conventional Commits",
    summary="Commit subjects must be `type(scope): summary`, ≤ 72 chars.",
    scope=on_event(EventType.COMMIT_CREATED),
    check=_check,
    price=Price.for_tier(CheckTier.STATIC),
    upstream=Upstream(repo="openharness/modules-conventional-commits", version="1.0.4"),
    tags=("workflow", "vcs"),
)
