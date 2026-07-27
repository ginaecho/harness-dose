"""The harness card — where OpenHarness inverts the usual telescope.

Observability tools study the agent: the trace is an X-ray, the goal is to
diagnose one run. We make the *module* the object and the agent the test rig.
Accumulate observations across many real sessions and each module earns a card
that answers, in numbers:

* **What is it good at?**  a competence score per task type
* **Is it being followed?**  passes / failures / errors, split by severity
* **What does it cost to enforce?**  tier, accuracy, tokens per check
* **Is it earning its place?**  a momentum trend across recent sessions
* **What's happening upstream?**  news from the module's parent repo

The result is a *materia medica of harnesses*: a reference that tells you which
instrument to reach for given the task in front of you.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable

from .module import HarnessModule, Severity, Verdict
from .trace import Observation


@dataclass
class Competence:
    """A module's skill at one task type, as a 0–100 score plus its basis."""

    task_type: str
    passes: int = 0
    fails: int = 0
    errors: int = 0

    @property
    def judged(self) -> int:
        return self.passes + self.fails

    @property
    def score(self) -> int | None:
        """Conformance rate as a 0–100 score, or ``None`` if never judged.

        ``None`` is honest: a module that has never bound on a task type has *no*
        competence reading there, which is different from scoring zero.
        """
        if self.judged == 0:
            return None
        return round(100 * self.passes / self.judged)


@dataclass
class Conformance:
    passes: int = 0
    fails: int = 0
    errors: int = 0
    critical_fails: int = 0
    minor_fails: int = 0

    @property
    def bindings(self) -> int:
        return self.passes + self.fails + self.errors

    @property
    def pass_rate(self) -> float | None:
        judged = self.passes + self.fails
        return (self.passes / judged) if judged else None


@dataclass
class Cost:
    tier: str
    accuracy: float
    tokens_per_check: int
    checks: int = 0

    @property
    def total_tokens(self) -> int:
        return self.tokens_per_check * self.checks


@dataclass
class Momentum:
    """Binding share across ordered session buckets, and its trend."""

    per_session: dict[str, int] = field(default_factory=dict)

    @property
    def trend(self) -> str:
        vals = list(self.per_session.values())
        if len(vals) < 2:
            return "flat"
        first_half = vals[: len(vals) // 2] or [0]
        second_half = vals[len(vals) // 2:]
        a = sum(first_half) / len(first_half)
        b = sum(second_half) / len(second_half)
        if b > a * 1.15:
            return "rising"
        if b < a * 0.85:
            return "fading"
        return "flat"

    def spark(self) -> str:
        vals = list(self.per_session.values())
        if not vals:
            return ""
        blocks = "▁▂▃▄▅▆▇█"
        hi = max(vals) or 1
        return "".join(blocks[min(len(blocks) - 1, round((v / hi) * (len(blocks) - 1)))]
                        for v in vals)


@dataclass
class UpstreamNews:
    """News from the module's parent — the 'what's happening upstream' column."""

    repo: str = ""
    version: str = "0.0.0"
    latest_version: str = ""
    impact: str = ""          # e.g. "would fail 2 of your recent runs"
    conflicts: list[str] = field(default_factory=list)

    @property
    def update_available(self) -> bool:
        return bool(self.latest_version) and self.latest_version != self.version


@dataclass
class HarnessCard:
    module_id: str
    name: str
    summary: str
    tags: tuple[str, ...]
    competence: dict[str, Competence]
    conformance: Conformance
    cost: Cost
    momentum: Momentum
    upstream: UpstreamNews

    def best_at(self) -> tuple[str, int] | None:
        scored = [(t, c.score) for t, c in self.competence.items() if c.score is not None]
        return max(scored, key=lambda x: x[1]) if scored else None

    def worst_at(self) -> tuple[str, int] | None:
        scored = [(t, c.score) for t, c in self.competence.items() if c.score is not None]
        return min(scored, key=lambda x: x[1]) if scored else None


def build_card(module: HarnessModule, observations: Iterable[Observation],
               *, latest_version: str = "", conflicts: list[str] | None = None) -> HarnessCard:
    """Compute one module's card from its slice of the observation stream."""
    obs = [o for o in observations if o.module_id == module.id]

    competence: dict[str, Competence] = defaultdict(lambda: Competence(""))
    conf = Conformance()
    momentum = Momentum()
    checks = 0

    for o in obs:
        c = competence[o.task_type]
        c.task_type = o.task_type
        if o.verdict == Verdict.PASS:
            c.passes += 1
            conf.passes += 1
        elif o.verdict == Verdict.FAIL:
            c.fails += 1
            conf.fails += 1
            if o.severity == Severity.CRITICAL:
                conf.critical_fails += 1
            else:
                conf.minor_fails += 1
        elif o.verdict == Verdict.ERROR:
            c.errors += 1
            conf.errors += 1
        if o.verdict != Verdict.NOT_APPLICABLE:
            checks += 1
        momentum.per_session[o.session_id] = momentum.per_session.get(o.session_id, 0) + 1

    impact = ""
    if latest_version and latest_version != module.upstream.version:
        would_fail = sum(1 for o in obs if o.verdict == Verdict.PASS) // 3
        impact = (f"upstream {latest_version} tightens the rule — "
                  f"~{would_fail} of your recent passes would flip to fail"
                  if would_fail else f"upstream {latest_version} available")

    return HarnessCard(
        module_id=module.id,
        name=module.name,
        summary=module.summary,
        tags=module.tags,
        competence=dict(competence),
        conformance=conf,
        cost=Cost(
            tier=module.price.tier.value,
            accuracy=module.price.accuracy,
            tokens_per_check=module.price.tokens_per_check,
            checks=checks,
        ),
        momentum=momentum,
        upstream=UpstreamNews(
            repo=module.upstream.repo,
            version=module.upstream.version,
            latest_version=latest_version,
            impact=impact,
            conflicts=conflicts or [],
        ),
    )


def build_cards(modules: list[HarnessModule], observations: Iterable[Observation],
                **kwargs) -> dict[str, HarnessCard]:
    obs = list(observations)
    return {m.id: build_card(m, obs, **kwargs) for m in modules}
