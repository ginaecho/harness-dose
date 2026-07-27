"""Governance layer — precedence, static conflict detection, and a watcher.

The modules in ``modules/`` answer "was *this* rule followed?" one at a time.
But the failures that actually hurt come from **rule interaction**: two in-scope
rules contradict, and whoever resolves the contradiction picks an order — and if
the order is wrong, the agent does the wrong thing *while following a rule*.

This module adds the three things that turn a pile of rules into a governed
layer:

1. :class:`Directive` — a rule's demand on an action (REQUIRE / FORBID a
   property), tagged with the **source** it came from.
2. :func:`static_conflicts` — a FORGE-style (arXiv:2602.16708) static check that
   finds pairs of directives that cannot both be satisfied, *before* anything
   runs. This is the "conflict set" — a fifth output beside the usual
   trace/rule/LLM/policy tiers.
3. :class:`Watcher` — a policy engine, in the Microsoft agent-governance style,
   that observes an agent's **inputs and actions** (not just its final reply),
   resolves in-scope directives by a declared **precedence**, and records when a
   contradiction was resolved — so a conflict that used to be silent becomes a
   logged verdict.

Precedence fixes contradiction. It does **not** fix under-specification — an
ambiguous scope or an ambiguous authorization is not a contradiction, so it will
not appear in the conflict set. Those need different mechanisms (declarative
scope; a deterministic gate). The experiment in ``precedence/`` demonstrates
exactly which mechanism fixes which failure.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class Source(enum.Enum):
    """Where a rule comes from — the axis precedence orders."""

    CONVERSATION = "conversation"   # explicit in-conversation direction
    PROJECT = "project"             # AGENT.md / CLAUDE.md project rule files
    HARNESS = "harness"             # harness / system-prompt defaults


class Polarity(enum.Enum):
    REQUIRE = "require"
    FORBID = "forbid"


@dataclass(frozen=True)
class Directive:
    """One rule's demand on one property of an action."""

    module_id: str
    source: Source
    target: str          # e.g. "branch.name", "commit.trailer"
    polarity: Polarity
    value: str           # the token/pattern the polarity applies to
    message: str = ""


def contradicts(a: Directive, b: Directive) -> bool:
    """True iff two directives demand incompatible things of the same property.

    Deliberately narrow: same target, opposite polarity, same value. REQUIRE
    ``^gc/`` and FORBID ``claude`` on ``branch.name`` do *not* contradict (they
    can both hold); REQUIRE ``claude`` and FORBID ``claude`` do.
    """
    return (a.target == b.target
            and a.value == b.value
            and a.polarity != b.polarity)


def static_conflicts(directives: list[Directive]) -> list[tuple[Directive, Directive]]:
    """FORGE-style: enumerate contradicting directive pairs before any run."""
    pairs: list[tuple[Directive, Directive]] = []
    for i in range(len(directives)):
        for j in range(i + 1, len(directives)):
            if contradicts(directives[i], directives[j]):
                pairs.append((directives[i], directives[j]))
    return pairs


@dataclass
class AuditEntry:
    """The watcher's record for one observed action."""

    action_type: str
    target: str
    in_scope: list[Directive]
    winner: Directive | None
    conflict: bool               # ≥2 contradicting directives were in scope
    silently_resolved: bool      # a conflict existed but was not surfaced
    complied: bool
    detail: str = ""


def resolve_by_precedence(directives: list[Directive],
                          precedence: tuple[Source, ...]) -> Directive | None:
    """Pick the highest-precedence directive; ``precedence[0]`` wins ties."""
    if not directives:
        return None
    rank = {s: i for i, s in enumerate(precedence)}
    return min(directives, key=lambda d: rank.get(d.source, len(precedence)))
