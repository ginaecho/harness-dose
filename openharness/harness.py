"""The plugin layer itself — middleware that sits *above* the agent.

The agent underneath is unchanged: it keeps its task skills and does its work,
emitting events. The :class:`Harness` mounts a set of modules over that stream.
For every event it asks each module's scope whether it binds; if it does, it
runs the module's check against the task's event history and emits an
:class:`Observation`. The reins are held from outside — binding is the layer's
call, never the agent's.
"""

from __future__ import annotations

from collections import defaultdict

from .events import Event
from .module import HarnessModule, Verdict
from .trace import Observation, Trace


class Harness:
    """A mounted set of harness modules watching one or more sessions."""

    def __init__(self, modules: list[HarnessModule], session_id: str = "session"):
        self.modules = list(modules)
        self.session_id = session_id
        self.trace = Trace(session_id)
        # per-task rolling event history, so checks can look back over the task
        self._history: dict[str, list[Event]] = defaultdict(list)

    def mount(self, module: HarnessModule) -> None:
        self.modules.append(module)

    def unmount(self, module_id: str) -> None:
        self.modules = [m for m in self.modules if m.id != module_id]

    def observe(self, event: Event) -> list[Observation]:
        """Push one event through the layer, returning the observations it produced."""
        history = self._history[event.task_id]
        produced: list[Observation] = []
        for module in self.modules:
            binding = module.binds(event)
            if not binding.bound:
                continue
            outcome = module.conform(event, history + [event])
            obs = Observation(
                ts=event.ts,
                session_id=self.session_id,
                task_id=event.task_id,
                task_type=event.task_type,
                event_type=event.type,
                module_id=module.id,
                binding_evidence=binding.evidence,
                verdict=outcome.verdict,
                severity=outcome.severity,
                tokens=outcome.tokens,
                tier=module.price.tier.value,
                message=outcome.message,
                check_evidence=outcome.evidence,
            )
            self.trace.add(obs)
            produced.append(obs)
        # record the event only after checks run, so checks see history *before* it
        history.append(event)
        return produced

    def run(self, events: list[Event]) -> Trace:
        """Replay a whole session of events and return the completed trace."""
        for ev in events:
            self.observe(ev)
        return self.trace

    # -- convenience roll-ups -------------------------------------------------

    def failures(self) -> list[Observation]:
        return [o for o in self.trace if o.verdict == Verdict.FAIL]

    def total_tokens(self) -> int:
        return sum(o.tokens for o in self.trace)
