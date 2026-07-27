"""AGT integration tests — skipped automatically when AGT is not installed."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openharness.agt import (build_precedence_policy, evaluate_action, has_agt,
                             make_evaluator)

pytestmark = pytest.mark.skipif(not has_agt(),
                                reason="Microsoft AGT (agent-governance-toolkit-core) not installed")


def test_policy_compiles_from_precedence_modules():
    doc = build_precedence_policy()
    assert doc.rules, "expected compiled AGT rules"
    names = {r.name for r in doc.rules}
    assert any("branch-policy" in n for n in names)
    assert any("no-assistant-trailer" in n for n in names)


def test_precedence_denies_claude_branch_allows_gc():
    ev = make_evaluator()
    assert evaluate_action(ev, {"branch.name": "claude/x"})["allowed"] is False
    assert evaluate_action(ev, {"branch.name": "gc/x"})["allowed"] is True


def test_precedence_denies_assistant_trailer():
    ev = make_evaluator()
    assert evaluate_action(ev, {"commit.trailer": "coauthor"})["allowed"] is False
    assert evaluate_action(ev, {"commit.trailer": "none"})["allowed"] is True


def test_destructive_gate_blocks_ambiguous_authorization():
    ev = make_evaluator()
    assert evaluate_action(ev, {"authorization": "ambiguous"})["allowed"] is False
    assert evaluate_action(ev, {"authorization": "explicit"})["allowed"] is True


def test_project_rule_outranks_harness_default_by_priority():
    from openharness.agt import SOURCE_PRIORITY
    from openharness.govern import Source
    assert SOURCE_PRIORITY[Source.PROJECT] > SOURCE_PRIORITY[Source.HARNESS]
    assert SOURCE_PRIORITY[Source.CONVERSATION] > SOURCE_PRIORITY[Source.PROJECT]
