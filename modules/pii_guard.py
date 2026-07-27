"""pii-guard — no unmasked PII leaves a query.

Binds when a query touches a PII column; conforms only if that specific column
is wrapped in a masking/hashing call, or the query carries an explicit
approved-access marker. Static tier: it parses the SQL text, no model call
needed. Failures are critical.

Correctness notes (regression-tested by benchmark/agent_sim.py):
* columns are matched as whole words, so ``email_events`` (a table name) does
  not trip the ``email`` rule;
* masking is attributed *per column* — ``hash(email), ssn`` fails, because the
  masking call wraps ``email``, not the leaked ``ssn``.
"""

from __future__ import annotations

import re

from openharness.checks import on_event_when
from openharness.events import Event, EventType
from openharness.module import (CheckOutcome, CheckTier, HarnessModule, Price,
                                 Severity, Upstream)

PII_COLUMNS = ("email", "ssn", "phone", "dob", "address", "credit_card")
_MASK_FNS = r"(?:mask|hash|sha256|md5|redact|anonymize)"


def _pii_columns_present(sql: str) -> list[str]:
    return [c for c in PII_COLUMNS if re.search(rf"\b{c}\b", sql, re.IGNORECASE)]


def _touches_pii(ev: Event) -> bool:
    return bool(_pii_columns_present(ev.get("sql", "") or ""))


def _column_is_masked(sql: str, col: str) -> bool:
    """True iff every whole-word occurrence of ``col`` sits inside a masking call.

    Conservative by design: only the column *directly* inside ``mask(...)`` /
    ``hash(...)`` counts as masked, so proximity to another column's masking call
    never grants a free pass.
    """
    for m in re.finditer(rf"\b{re.escape(col)}\b", sql, re.IGNORECASE):
        before = sql[: m.start()]
        if not re.search(_MASK_FNS + r"\s*\(\s*$", before, re.IGNORECASE):
            return False
    return True


def _check(event: Event, history: list[Event]) -> CheckOutcome:
    sql = event.get("sql", "") or ""
    if event.get("approved_access"):
        return CheckOutcome.passed("carries an approved-access marker")
    named = _pii_columns_present(sql)
    leaked = [c for c in named if not _column_is_masked(sql, c)]
    if not leaked:
        return CheckOutcome.passed(f"PII columns masked: {', '.join(named)}")
    return CheckOutcome.failed(
        f"unmasked PII in query: {', '.join(leaked)}",
        evidence=sql.strip()[:120],
        severity=Severity.CRITICAL)


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
