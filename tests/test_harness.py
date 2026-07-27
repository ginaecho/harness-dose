import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openharness.events import EventType, event
from openharness.harness import Harness
from openharness.module import Verdict
from modules import ALL, tdd, pii_guard, no_secrets, conventional_commits, prose_style


def _verdicts(trace, module_id):
    return [o.verdict for o in trace.for_module(module_id)]


def test_tdd_binds_only_on_code_modified():
    h = Harness([tdd])
    assert tdd.binds(event(EventType.CODE_MODIFIED, "t", "bug_fix")).bound
    assert not tdd.binds(event(EventType.DOC_WRITTEN, "t", "bug_fix")).bound


def test_tdd_passes_when_failing_test_precedes_code():
    h = Harness([tdd])
    h.observe(event(EventType.TEST_WRITTEN, "t", "bug_fix", status="failing"))
    h.observe(event(EventType.CODE_MODIFIED, "t", "bug_fix"))
    assert _verdicts(h.trace, "tdd") == [Verdict.PASS]


def test_tdd_fails_when_code_comes_first():
    h = Harness([tdd])
    h.observe(event(EventType.CODE_MODIFIED, "t", "bug_fix"))
    assert _verdicts(h.trace, "tdd") == [Verdict.FAIL]


def test_history_isolated_per_task():
    # a failing test in task A must not satisfy tdd for task B
    h = Harness([tdd])
    h.observe(event(EventType.TEST_WRITTEN, "A", "bug_fix", status="failing"))
    h.observe(event(EventType.CODE_MODIFIED, "B", "bug_fix"))
    assert _verdicts(h.trace, "tdd") == [Verdict.FAIL]


def test_pii_guard_catches_unmasked_and_passes_masked():
    h = Harness([pii_guard])
    h.observe(event(EventType.QUERY_EXECUTED, "t", "data", sql="SELECT email FROM users"))
    h.observe(event(EventType.QUERY_EXECUTED, "t", "data", sql="SELECT hash(email) FROM users"))
    assert _verdicts(h.trace, "pii-guard") == [Verdict.FAIL, Verdict.PASS]


def test_pii_guard_does_not_bind_without_pii():
    assert not pii_guard.binds(
        event(EventType.QUERY_EXECUTED, "t", "data", sql="SELECT count(*) FROM orders")).bound


def test_no_secrets_flags_aws_key_critical():
    h = Harness([no_secrets])
    h.observe(event(EventType.FILE_WRITTEN, "t", "refactor",
                    content='API_KEY = "AKIAIOSFODNN7EXAMPLE"'))
    obs = h.trace.for_module("no-secrets")[0]
    assert obs.verdict == Verdict.FAIL
    assert obs.severity.value == "critical"


def test_conventional_commits():
    h = Harness([conventional_commits])
    h.observe(event(EventType.COMMIT_CREATED, "t", "bug_fix", message="fix(x): ok"))
    h.observe(event(EventType.COMMIT_CREATED, "t", "bug_fix", message="did stuff"))
    assert _verdicts(h.trace, "conventional-commits") == [Verdict.PASS, Verdict.FAIL]


def test_prose_style_judge_flags_hype():
    h = Harness([prose_style])
    h.observe(event(EventType.DOC_WRITTEN, "t", "docs",
                    content="Blazing revolutionary game-changing seamless 10x."))
    assert _verdicts(h.trace, "prose-style") == [Verdict.FAIL]


def test_priced_tier_stamps_tokens():
    h = Harness([prose_style])
    h.observe(event(EventType.DOC_WRITTEN, "t", "docs", content="A clear, plain sentence."))
    assert h.trace.for_module("prose-style")[0].tokens == 1200


def test_free_tier_costs_nothing():
    h = Harness([tdd])
    h.observe(event(EventType.TEST_WRITTEN, "t", "bug_fix", status="failing"))
    h.observe(event(EventType.CODE_MODIFIED, "t", "bug_fix"))
    assert h.total_tokens() == 0


def test_broken_check_surfaces_as_error_not_crash():
    from openharness.module import HarnessModule, Price, CheckTier
    from openharness.checks import on_event

    def boom(ev, hist):
        raise ValueError("nope")

    m = HarnessModule("boom", "Boom", "", on_event(EventType.CODE_MODIFIED), boom,
                      Price.for_tier(CheckTier.DETERMINISTIC))
    h = Harness([m])
    h.observe(event(EventType.CODE_MODIFIED, "t", "bug_fix"))
    assert h.trace.for_module("boom")[0].verdict == Verdict.ERROR
