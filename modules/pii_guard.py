"""pii-guard — no unmasked PII leaves a query.

Binds when a query touches a PII column; conforms only if the query masks or
hashes that column, or carries an explicit approved-access marker. Static tier:
it parses the SQL text, no model call needed. Failures are critical.
"""

from __future__ import annotations

import re

from openharness.checks import on_event_when
from openharness.events import Event, EventType
from openharness.module import (CheckOutcome, CheckTier, HarnessModule, Price,
                                 Severity, Upstream)

PII_COLUMNS = ("email", "ssn", "phone", "dob", "address", "credit_card")
_MASKED = re.compile(r"\b(mask|hash|sha256|redact|anonymize|md5)\s*\(", re.IGNORECASE)


def _touches_pii(ev: Event) -> bool:
    sql = (ev.get("sql", "") or "").lower()
    return any(col in sql for col in PII_COLUMNS)


def _check(event: Event, history: list[Event]) -> CheckOutcome:
    sql = event.get("sql", "") or ""
    if event.get("approved_access"):
        return CheckOutcome.passed("carries an approved-access marker")
    named = [c for c in PII_COLUMNS if c in sql.lower()]
    unmasked = [c for c in named
                if not _MASKED.search(sql[:_index_after(sql, c)] + sql)]
    # a column is fine if it appears only inside a masking call
    truly_unmasked = [c for c in named if not _column_is_masked(sql, c)]
    if not truly_unmasked:
        return CheckOutcome.passed(f"PII columns masked: {', '.join(named)}")
    return CheckOutcome.failed(
        f"unmasked PII in query: {', '.join(truly_unmasked)}",
        evidence=sql.strip()[:120],
        severity=Severity.CRITICAL)


def _index_after(sql: str, col: str) -> int:
    i = sql.lower().find(col)
    return i + len(col) if i >= 0 else len(sql)


def _column_is_masked(sql: str, col: str) -> bool:
    # true if every occurrence of the column sits within a masking call
    for m in re.finditer(re.escape(col), sql, re.IGNORECASE):
        window = sql[max(0, m.start() - 40): m.start()]
        if not _MASKED.search(window):
            return False
    return True


MODULE = HarnessModule(
    id="pii-guard",
    name="PII Guard",
    summary="Queries touching PII must mask, hash, or carry approved access.",
    scope=on_event_when(EventType.QUERY_EXECUTED, _touches_pii,
                        because="SQL references a PII column"),
    check=_check,
    price=Price.for_tier(CheckTier.STATIC),
    upstream=Upstream(repo="openharness/modules-pii-guard", version="2.0.1"),
    tags=("security", "data", "compliance"),
)
