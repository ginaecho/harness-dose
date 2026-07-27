"""End-to-end demo: mount the modules, replay real-looking sessions, print the
verdict stream, and emit a harness-cards dashboard.

Run it::

    python -m examples.demo_session          # prints the stream + writes dashboard.html
    python examples/demo_session.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openharness.card import build_cards
from openharness.dashboard import render_dashboard
from openharness.evaluate import LabeledRun, measure_accuracy, on_off_delta
from openharness.events import EventType, event
from openharness.harness import Harness
from modules import ALL, tdd


# --- scenario builders -------------------------------------------------------
# Each returns a session's worth of events. "task_type" is what lets the cards
# say tdd is great at bug_fix but useless at prototyping.

def bug_fix(task_id: str, *, tdd_followed: bool):
    t, tt = task_id, "bug_fix"
    evs = []
    if tdd_followed:
        evs.append(event(EventType.TEST_WRITTEN, t, tt, name="test_regression", status="failing"))
    evs.append(event(EventType.CODE_MODIFIED, t, tt, files=["bug.py"], lines=12))
    evs.append(event(EventType.COMMIT_CREATED, t, tt,
                     message="fix(parser): handle empty input" if tdd_followed
                     else "fixed the bug"))
    return evs


def prototype(task_id: str):
    t, tt = task_id, "prototype"
    # prototypes move fast and skip tests on purpose — tdd will (correctly) score low here
    return [
        event(EventType.CODE_MODIFIED, t, tt, files=["spike.py"], lines=140),
        event(EventType.FILE_WRITTEN, t, tt, path="spike.py", content="print('hello')"),
        event(EventType.COMMIT_CREATED, t, tt, message="wip: trying an idea"),
    ]


def data_analysis(task_id: str, *, masked: bool):
    t, tt = task_id, "data_analysis"
    sql = ("SELECT hash(email), count(*) FROM users GROUP BY 1" if masked
           else "SELECT email, ssn FROM users WHERE signup > '2025-01-01'")
    return [
        event(EventType.QUERY_EXECUTED, t, tt, sql=sql),
        event(EventType.DOC_WRITTEN, t, tt,
              content=("Signups rose 12% quarter over quarter; the trend is "
                       "steady across cohorts and holds after excluding refunds.")),
    ]


def refactor(task_id: str, *, clean: bool):
    t, tt = task_id, "refactor"
    content = ("def add(a, b):\n    return a + b\n" if clean
               else 'API_KEY = "AKIAIOSFODNN7EXAMPLE"\n')
    return [
        event(EventType.TEST_RUN, t, tt, status="failing"),
        event(EventType.CODE_MODIFIED, t, tt, files=["util.py"], lines=30),
        event(EventType.FILE_WRITTEN, t, tt, path="util.py", content=content),
        event(EventType.COMMIT_CREATED, t, tt, message="refactor(util): extract helper"),
    ]


def docs(task_id: str, *, hype: bool):
    t, tt = task_id, "docs"
    content = ("Our blazing, revolutionary, game-changing platform delivers "
               "seamless, effortless, world-class results at 10x the speed."
               if hype else
               "This module mounts a rule above the agent and records whether it "
               "was followed. Each check states its cost.")
    return [event(EventType.DOC_WRITTEN, t, tt, content=content)]


# --- build several sessions so momentum has something to trend over ----------

def sessions():
    return {
        "session-1": (bug_fix("t1", tdd_followed=True) + prototype("t2")
                      + data_analysis("t3", masked=False)),
        "session-2": (bug_fix("t4", tdd_followed=True) + bug_fix("t5", tdd_followed=False)
                      + refactor("t6", clean=False) + docs("t7", hype=True)),
        "session-3": (bug_fix("t8", tdd_followed=True) + data_analysis("t9", masked=True)
                      + refactor("t10", clean=True) + docs("t11", hype=False)
                      + prototype("t12")),
    }


def main() -> None:
    all_obs = []
    print("=" * 78)
    print("OBSERVABLE VERDICT STREAM  (event → module bound → verdict)")
    print("=" * 78)
    for sid, events in sessions().items():
        h = Harness(ALL, session_id=sid)
        h.run(events)
        print(f"\n── {sid} " + "─" * (72 - len(sid)))
        for o in h.trace:
            print("  " + o.render_line())
        all_obs.extend(h.trace.observations)

    # Testable: what does mounting tdd add on this session, vs having it off?
    print("\n" + "=" * 78)
    print("A/B — on/off delta for `tdd` on session-2")
    print("=" * 78)
    others = [m for m in ALL if m.id != "tdd"]
    delta = on_off_delta(tdd, others, sessions()["session-2"])
    print("  " + delta.summary())

    # Testable: measured accuracy against labeled fixtures
    runs = [
        LabeledRun(bug_fix("l1", tdd_followed=True), compliant=True),
        LabeledRun(bug_fix("l2", tdd_followed=False), compliant=False),
        LabeledRun(bug_fix("l3", tdd_followed=True), compliant=True),
        LabeledRun(prototype("l4"), compliant=False),
    ]
    acc = measure_accuracy(tdd, runs)
    print(f"  tdd measured accuracy: {acc.accuracy:.0%} "
          f"({acc.correct}/{acc.samples}; fp={acc.false_pos} fn={acc.false_neg})")

    # Cards + dashboard. Pretend pii-guard has an upstream release with impact.
    cards = build_cards(ALL, all_obs, latest_version="", conflicts=None)
    # inject a bit of upstream news for the demo narrative
    from openharness.card import build_card
    cards["pii-guard"] = build_card(
        next(m for m in ALL if m.id == "pii-guard"), all_obs,
        latest_version="2.1.0", conflicts=[])

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dashboard.html")
    out = os.path.abspath(out)
    with open(out, "w") as f:
        f.write(render_dashboard(cards.values()))

    print("\n" + "=" * 78)
    print("HARNESS CARDS (text summary)")
    print("=" * 78)
    for c in cards.values():
        best, worst = c.best_at(), c.worst_at()
        pr = c.conformance.pass_rate
        print(f"\n  {c.name}  [{c.cost.tier} · acc {c.cost.accuracy:.0%} · "
              f"{c.cost.tokens_per_check} tok/check]")
        print(f"    conformance: {pr*100:.0f}% pass  "
              f"({c.conformance.passes}✓ {c.conformance.fails}✗ "
              f"{c.conformance.critical_fails} critical)"
              if pr is not None else "    conformance: no data")
        if best:
            print(f"    best at {best[0]} ({best[1]}) · weakest at "
                  f"{worst[0]} ({worst[1]})" if worst else f"    best at {best[0]} ({best[1]})")
        print(f"    momentum: {c.momentum.spark()} ({c.momentum.trend})")

    print(f"\n✓ dashboard written to {out}\n")


if __name__ == "__main__":
    main()
