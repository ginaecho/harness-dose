"""prose-style — docs read clearly and without hype.

Binds when a document is written; a judge scores clarity and flags hype words.
LLM-judge tier: this verdict carries a price and a *stated accuracy* (0.85) —
unlike the deterministic and static modules, it can be wrong, and the card says
so out loud.

In this reproducible demo the "judge" is a deterministic scorer over the text so
the numbers replay identically; in production the same interface would call a
model. The point OpenHarness makes is architectural: the priced, fallible check
is a first-class, measured thing, not a hidden influence.
"""

from __future__ import annotations

import re

from openharness.checks import on_event
from openharness.events import Event, EventType
from openharness.module import (CheckOutcome, CheckTier, HarnessModule, Price,
                                 Severity, Upstream)

_HYPE = ("blazing", "revolutionary", "game-changing", "seamless", "effortless",
         "cutting-edge", "world-class", "leverage synergies", "10x")


def _score(text: str) -> tuple[float, str]:
    """A cheap, deterministic stand-in for a prose-quality judge (0–100)."""
    words = re.findall(r"\w+", text)
    if not words:
        return 0.0, "empty document"
    hype = sum(text.lower().count(h) for h in _HYPE)
    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    avg_len = len(words) / sentences
    score = 100.0
    score -= hype * 18                       # hype words hurt a lot
    score -= max(0, avg_len - 28) * 2        # runaway sentences hurt
    rationale = []
    if hype:
        rationale.append(f"{hype} hype word(s)")
    if avg_len > 28:
        rationale.append(f"avg sentence {avg_len:.0f} words")
    if not rationale:
        rationale.append("clear and hype-free")
    return max(0.0, min(100.0, score)), "; ".join(rationale)


def _check(event: Event, history: list[Event]) -> CheckOutcome:
    text = event.get("content", "") or ""
    score, rationale = _score(text)
    threshold = 70.0
    if score >= threshold:
        return CheckOutcome.passed(f"judge {score:.0f} ≥ {threshold:.0f}: {rationale}")
    return CheckOutcome.failed(
        f"judge {score:.0f} < {threshold:.0f}: {rationale}", severity=Severity.MINOR)


MODULE = HarnessModule(
    id="prose-style",
    name="Prose Style",
    summary="Documentation must read clearly and avoid hype (judged, ~85% accurate).",
    scope=on_event(EventType.DOC_WRITTEN),
    check=_check,
    price=Price.for_tier(CheckTier.LLM_JUDGE, accuracy=0.85, tokens_per_check=1200),
    upstream=Upstream(repo="openharness/modules-prose-style", version="0.4.2"),
    tags=("writing", "docs"),
)
