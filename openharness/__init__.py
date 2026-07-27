"""OpenHarness — see the harness, share the harness, prove the harness works.

Behavioral rules are lifted out of an agent's skills and re-mounted as a plugin
layer above it. Each rule becomes a *harness module* with a declared scope, a
conformance check, and a price. The layer decides binding — not the agent — and
logs an observable stream of verdicts, from which every module earns a
*harness card*.

Quick start::

    from openharness import Harness
    from openharness.events import event, EventType
    from modules import ALL

    h = Harness(ALL)
    for ev in my_session_events:
        for obs in h.observe(ev):
            print(obs.render_line())

    from openharness.card import build_cards
    from openharness.dashboard import render_dashboard
    cards = build_cards(ALL, h.trace)
    open("dashboard.html", "w").write(render_dashboard(cards.values()))
"""

from __future__ import annotations

from .card import HarnessCard, build_card, build_cards
from .dashboard import render_dashboard
from .events import Event, EventType, event
from .harness import Harness
from .module import (Binding, CheckOutcome, CheckTier, HarnessModule, Price,
                     Severity, Upstream, Verdict)
from .trace import Observation, Trace

__version__ = "0.1.0"

__all__ = [
    "Harness", "HarnessModule", "Event", "EventType", "event",
    "Binding", "CheckOutcome", "CheckTier", "Price", "Severity", "Upstream", "Verdict",
    "Observation", "Trace",
    "HarnessCard", "build_card", "build_cards", "render_dashboard",
    "__version__",
]
