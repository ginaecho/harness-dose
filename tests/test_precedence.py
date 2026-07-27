import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openharness.govern import (Polarity, Source, contradicts,
                                resolve_by_precedence, static_conflicts, Directive)
from precedence.experiment import (BAD_ORDER, CONDITIONS, RIGHT_ORDER,
                                   precedence_sweep, run, violates)
from precedence.rules import all_directives
from precedence.scenarios import SKILLS


def _cond(name):
    return next(c for c in CONDITIONS if c.name == name)


def test_static_scan_finds_exactly_the_two_contradictions():
    conflicts = static_conflicts(all_directives())
    assert len(conflicts) == 2
    targets = {a.target for a, b in conflicts}
    assert targets == {"branch.name", "commit.trailer"}


def test_underspecified_rules_not_in_conflict_set():
    # reply.style (C3) and authorization (C4) have no contradicting counterpart
    conflicts = static_conflicts(all_directives())
    involved = {d.target for pair in conflicts for d in pair}
    assert "reply.style" not in involved
    assert "authorization" not in involved


def test_contradicts_is_narrow():
    a = Directive("m", Source.PROJECT, "branch.name", Polarity.FORBID, "claude")
    b = Directive("m", Source.HARNESS, "branch.name", Polarity.REQUIRE, "claude")
    c = Directive("m", Source.PROJECT, "branch.name", Polarity.REQUIRE, "^gc/")
    assert contradicts(a, b)
    assert not contradicts(a, c)   # forbid claude vs require gc/ can both hold


def test_resolve_by_precedence_picks_top_source():
    ds = [Directive("h", Source.HARNESS, "x", Polarity.REQUIRE, "claude/b"),
          Directive("p", Source.PROJECT, "x", Polarity.REQUIRE, "gc/b")]
    assert resolve_by_precedence(ds, BAD_ORDER).value == "claude/b"
    assert resolve_by_precedence(ds, RIGHT_ORDER).value == "gc/b"


def test_embedded_fails_every_skill():
    grid, _silent, _logged = run()
    for skill in SKILLS:
        assert grid[(skill.name, "embedded")], skill.name


def test_externalizing_alone_does_not_fix_ordering():
    # bad order externalized: scope+gate fix C3/C4, but C1/C2 remain
    grid, _s, _l = run()
    for skill in SKILLS:
        fails = set(grid[(skill.name, "externalized, bad order")])
        assert "C3" not in fails and "C4" not in fails
        # any skill with a contested action still fails C1 or C2
        classes = {a.failure_class for a in skill.actions}
        if classes & {"C1", "C2"}:
            assert fails & {"C1", "C2"}


def test_right_order_clears_all_skills():
    grid, _s, _l = run()
    for skill in SKILLS:
        assert grid[(skill.name, "externalized, right order")] == []


def test_conflicts_logged_not_silent_when_externalized():
    _grid, silent, logged = run()
    assert silent > 0 and logged > 0   # same contradictions, hidden vs recorded


def test_precedence_sweep_project_above_harness_wins():
    sweep = precedence_sweep()
    winners = [perm for perm, total in sweep if total == 0]
    losers = [perm for perm, total in sweep if total > 0]
    assert winners and losers
    for perm in winners:
        assert perm.index(Source.PROJECT) < perm.index(Source.HARNESS)
    for perm in losers:
        assert perm.index(Source.HARNESS) < perm.index(Source.PROJECT)
