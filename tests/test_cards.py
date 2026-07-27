import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openharness.card import build_cards
from openharness.dashboard import render_dashboard
from openharness.evaluate import LabeledRun, measure_accuracy, on_off_delta
from openharness.events import EventType, event
from openharness.harness import Harness
from modules import ALL, tdd


def _bugfix(tid, ok):
    evs = []
    if ok:
        evs.append(event(EventType.TEST_WRITTEN, tid, "bug_fix", status="failing"))
    evs.append(event(EventType.CODE_MODIFIED, tid, "bug_fix"))
    return evs


def test_competence_differs_by_task_type():
    # tdd passes on bug_fix (test first) but fails on prototype (no test)
    obs = []
    h = Harness([tdd], session_id="s1")
    h.run(_bugfix("a", True) + [event(EventType.CODE_MODIFIED, "b", "prototype")])
    obs.extend(h.trace.observations)
    cards = build_cards([tdd], obs)
    comp = cards["tdd"].competence
    assert comp["bug_fix"].score == 100
    assert comp["prototype"].score == 0


def test_score_is_none_when_unexercised():
    obs = []
    h = Harness([tdd], session_id="s1")
    h.run(_bugfix("a", True))
    cards = build_cards([tdd], h.trace.observations)
    # refactor never happened → no reading
    assert "refactor" not in cards["tdd"].competence


def test_on_off_delta_counts_added_checks():
    others = [m for m in ALL if m.id != "tdd"]
    events = _bugfix("a", False)  # code with no test → tdd should catch it
    delta = on_off_delta(tdd, others, events)
    assert delta.checks_added == 1
    assert delta.failures_caught == 1


def test_measure_accuracy_perfect_on_deterministic():
    runs = [
        LabeledRun(_bugfix("a", True), compliant=True),
        LabeledRun(_bugfix("b", False), compliant=False),
        LabeledRun(_bugfix("c", True), compliant=True),
    ]
    rep = measure_accuracy(tdd, runs)
    assert rep.accuracy == 1.0


def test_momentum_trend():
    obs = []
    for i, sid in enumerate(["s1", "s2", "s3"]):
        h = Harness([tdd], session_id=sid)
        # more bindings each session → rising
        h.run(sum((_bugfix(f"{sid}-{j}", True) for j in range(i + 1)), []))
        obs.extend(h.trace.observations)
    cards = build_cards([tdd], obs)
    assert cards["tdd"].momentum.trend == "rising"


def test_dashboard_renders_all_cards():
    obs = []
    h = Harness(ALL, session_id="s1")
    h.run(_bugfix("a", True))
    cards = build_cards(ALL, h.trace.observations)
    html = render_dashboard(cards.values())
    assert "<!doctype html>" in html
    for m in ALL:
        assert m.name in html
    assert "Harness Cards" in html
