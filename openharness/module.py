"""Core vocabulary of the harness layer.

A *harness module* is a behavioral rule lifted out of an agent's skills and
re-mounted above it. Where a skill says *what* the agent does, a module says
*how* it must be done — and, crucially, the module is a first-class object with
a declared **scope** (when it binds), a **conformance check** (was it followed),
and a **price** (what the check costs to run).

Nothing here reaches into an agent. These are the nouns the layer reasons over.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Callable, Optional

from .events import Event


class CheckTier(enum.Enum):
    """How a conformance check is computed, and therefore what it costs.

    The tier is a *price tag*, not a quality ranking. A deterministic trace
    check is free and exact; an LLM judge is priced and only as accurate as its
    stated accuracy. A card shows the tier so enforcement cost is displayed,
    not hoped for.
    """

    DETERMINISTIC = "deterministic"  # reads the trace; exact; ~free
    STATIC = "static"                # a static rule (regex/parse); cheap
    LLM_JUDGE = "llm_judge"          # a model call; priced; stated accuracy

    @property
    def default_accuracy(self) -> float:
        return {
            CheckTier.DETERMINISTIC: 1.0,
            CheckTier.STATIC: 0.97,
            CheckTier.LLM_JUDGE: 0.85,
        }[self]

    @property
    def default_tokens(self) -> int:
        return {
            CheckTier.DETERMINISTIC: 0,
            CheckTier.STATIC: 0,
            CheckTier.LLM_JUDGE: 1200,
        }[self]


class Severity(enum.Enum):
    CRITICAL = "critical"
    MINOR = "minor"


class Verdict(enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"            # the check itself blew up
    NOT_APPLICABLE = "n/a"     # bound, but nothing to judge yet


@dataclass(frozen=True)
class Price:
    """The displayed cost of enforcing a module, once per check."""

    tier: CheckTier
    accuracy: float
    tokens_per_check: int

    @classmethod
    def for_tier(cls, tier: CheckTier, accuracy: Optional[float] = None,
                 tokens_per_check: Optional[int] = None) -> "Price":
        return cls(
            tier=tier,
            accuracy=tier.default_accuracy if accuracy is None else accuracy,
            tokens_per_check=(tier.default_tokens
                              if tokens_per_check is None else tokens_per_check),
        )


@dataclass(frozen=True)
class Binding:
    """The layer's decision that a module applies to an event.

    Binding is decided by the layer, not by the agent's discretion — so the
    ``evidence`` string records *why* it bound. That evidence is what makes the
    stream auditable.
    """

    bound: bool
    evidence: str = ""

    @classmethod
    def yes(cls, evidence: str) -> "Binding":
        return cls(True, evidence)

    @classmethod
    def no(cls) -> "Binding":
        return cls(False, "")

    def __bool__(self) -> bool:  # allows `if scope(event):`
        return self.bound


@dataclass(frozen=True)
class CheckOutcome:
    """The result of running a conformance check against the trace so far."""

    verdict: Verdict
    message: str = ""
    evidence: str = ""
    severity: Severity = Severity.MINOR
    tokens: int = 0

    @classmethod
    def passed(cls, message: str = "", evidence: str = "", tokens: int = 0) -> "CheckOutcome":
        return cls(Verdict.PASS, message, evidence, Severity.MINOR, tokens)

    @classmethod
    def failed(cls, message: str, evidence: str = "",
               severity: Severity = Severity.MINOR, tokens: int = 0) -> "CheckOutcome":
        return cls(Verdict.FAIL, message, evidence, severity, tokens)

    @classmethod
    def na(cls, message: str = "") -> "CheckOutcome":
        return cls(Verdict.NOT_APPLICABLE, message)


# A scope reads an event and decides whether the module binds.
ScopeFn = Callable[[Event], Binding]
# A check reads the current event plus the task's event history and judges it.
CheckFn = Callable[[Event, "list[Event]"], CheckOutcome]


@dataclass(frozen=True)
class Upstream:
    """Where a module comes from — its parent, for the 'news' column."""

    repo: str = ""
    version: str = "0.0.0"
    homepage: str = ""


@dataclass(frozen=True)
class HarnessModule:
    """A behavioral rule as a mountable unit.

    The three things a skill buried in prose could never give you: a ``scope``
    you can point at, a ``check`` you can run, and a ``price`` you can read.
    """

    id: str
    name: str
    summary: str
    scope: ScopeFn
    check: CheckFn
    price: Price
    upstream: Upstream = field(default_factory=Upstream)
    tags: tuple[str, ...] = ()

    def binds(self, event: Event) -> Binding:
        try:
            return self.scope(event)
        except Exception as exc:  # a broken scope must not sink the layer
            return Binding.no()

    def conform(self, event: Event, history: list[Event]) -> CheckOutcome:
        try:
            outcome = self.check(event, history)
        except Exception as exc:  # a broken check surfaces as ERROR, not a crash
            return CheckOutcome(
                Verdict.ERROR,
                message=f"check raised {type(exc).__name__}: {exc}",
                severity=Severity.CRITICAL,
            )
        # stamp the module's token price onto priced tiers if the check left it 0
        if outcome.tokens == 0 and self.price.tokens_per_check:
            outcome = CheckOutcome(
                outcome.verdict, outcome.message, outcome.evidence,
                outcome.severity, self.price.tokens_per_check,
            )
        return outcome
