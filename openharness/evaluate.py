"""Testability: a module is a unit, so evaluate it like one.

Two measurements the spec asks for:

* **On/off delta** — run the same task events with the module mounted and with
  it removed, and report what the module *added*: the verdicts that only exist
  because it was there.
* **Measured accuracy** — feed the module labeled runs (each known-compliant or
  known-violating) and check whether its verdict matches the label. This is how
  a card's stated accuracy stops being a guess.
"""

from __future__ import annotations

from dataclasses import dataclass

from .events import Event
from .harness import Harness
from .module import HarnessModule, Verdict


@dataclass
class OnOffDelta:
    module_id: str
    checks_added: int
    failures_caught: int
    tokens_spent: int

    def summary(self) -> str:
        return (f"{self.module_id}: +{self.checks_added} checks, "
                f"{self.failures_caught} violations caught, "
                f"{self.tokens_spent} tokens")


def on_off_delta(module: HarnessModule, others: list[HarnessModule],
                 events: list[Event]) -> OnOffDelta:
    """What does mounting ``module`` add on top of ``others`` for this session?"""
    without = Harness(others, session_id="off").run(events)
    with_ = Harness(others + [module], session_id="on").run(events)
    added = [o for o in with_ if o.module_id == module.id]
    return OnOffDelta(
        module_id=module.id,
        checks_added=len(added),
        failures_caught=sum(1 for o in added if o.verdict == Verdict.FAIL),
        tokens_spent=sum(o.tokens for o in added),
    )


@dataclass
class LabeledRun:
    """A task's events plus ground truth: did the agent actually follow the rule?"""

    events: list[Event]
    compliant: bool
    task_type: str = ""


@dataclass
class AccuracyReport:
    module_id: str
    samples: int
    correct: int
    false_pos: int   # said fail, was compliant
    false_neg: int   # said pass, was violating

    @property
    def accuracy(self) -> float:
        return self.correct / self.samples if self.samples else 0.0


def measure_accuracy(module: HarnessModule, runs: list[LabeledRun]) -> AccuracyReport:
    """Run the module against labeled fixtures and score its verdicts vs truth."""
    correct = fp = fn = 0
    for run in runs:
        h = Harness([module], session_id="eval")
        trace = h.run(run.events)
        verdicts = [o.verdict for o in trace.for_module(module.id)]
        # a run is judged "violating" if the module ever failed it
        said_fail = Verdict.FAIL in verdicts
        module_says_compliant = not said_fail
        if module_says_compliant == run.compliant:
            correct += 1
        elif said_fail and run.compliant:
            fp += 1
        else:
            fn += 1
    return AccuracyReport(module.id, len(runs), correct, fp, fn)
