import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.agent_sim import ABLATION_SUITE, corpus, perform
from benchmark.l1_conformance import evaluate as l1_evaluate
from benchmark.l2_ablation import _decisions, run_gated, run_off
from benchmark.metrics import Confusion


def test_metrics_confusion_math():
    c = Confusion()
    c.add(truth_violating=True, predicted_violating=True)   # TP
    c.add(truth_violating=False, predicted_violating=True)  # FP
    c.add(truth_violating=True, predicted_violating=False)  # FN
    c.add(truth_violating=False, predicted_violating=False)  # TN
    assert (c.tp, c.fp, c.fn, c.tn) == (1, 1, 1, 1)
    assert c.precision == 0.5 and c.recall == 0.5
    assert abs(c.f1 - 0.5) < 1e-9
    assert c.accuracy == 0.5


def test_corpus_has_adversarial_cases_and_labels():
    runs = corpus()
    assert len(runs) >= 30
    assert any("adversarial" in r.variant for r in runs)
    assert any(r.truth_violating for r in runs) and any(not r.truth_violating for r in runs)


def test_l1_is_perfect_after_pii_fix():
    # the whole point of L1: every module classifies the corpus (incl.
    # adversarial near-misses) correctly, so overall F1 == 1.0
    per_module, _per_tt, rows = l1_evaluate()
    overall = Confusion()
    for c in per_module.values():
        overall = overall.merge(c)
    assert overall.fp == 0 and overall.fn == 0, \
        [(r.module_id, r.variant) for r, p in rows if r.truth_violating != p]
    assert overall.f1 == 1.0


def test_pii_guard_regression_ssn_leak_and_table_name():
    # the two bugs L1 originally exposed, pinned as regression tests
    from openharness.harness import Harness
    from openharness.module import Verdict
    from modules import pii_guard
    from openharness.events import EventType, event

    # 1) ssn leak beside a masked email must be caught (binds + FAILs)
    h = Harness([pii_guard])
    h.observe(event(EventType.QUERY_EXECUTED, "t", "d", sql="SELECT hash(email), ssn FROM users"))
    assert [o.verdict for o in h.trace.for_module("pii-guard")] == [Verdict.FAIL]

    # 2) 'email' inside a table name must not even bind (no false alarm at all)
    assert not pii_guard.binds(
        event(EventType.QUERY_EXECUTED, "t2", "d", sql="SELECT count(*) FROM email_events")).bound


def test_l2_gating_removes_violations_without_hurting_success():
    d = _decisions(0)
    off = run_off(d)
    gated = run_gated(d)
    assert off.residual_violations > 0        # off leaves violations
    assert gated.residual_violations == 0     # gating removes them
    assert gated.success_rate == 1.0          # without lowering success


def test_l2_identical_decisions_isolate_the_intervention():
    # same seed → same agent choices in both arms; only gating differs
    d1, d2 = _decisions(7), _decisions(7)
    assert d1 == d2


def test_perform_produces_violation_when_not_complying():
    from openharness.harness import Harness
    from openharness.module import Verdict
    from modules import ALL
    mods = {m.id: m for m in ALL}
    for task in ABLATION_SUITE:
        evs = perform(task, comply=False)
        h = Harness([mods[task.module_id]])
        h.run(evs)
        assert any(o.verdict == Verdict.FAIL for o in h.trace), task
