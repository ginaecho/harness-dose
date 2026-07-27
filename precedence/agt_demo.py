"""Run the OpenHarness precedence scenario on Microsoft AGT's real engine.

Compiles the four lifted rules into an AGT ``PolicyDocument`` and evaluates the
contested actions from skills A–D through AGT's ``PolicyEvaluator`` — showing the
same verdicts as the native L5, but enforced by Microsoft's engine via
priority-based conflict resolution.

    python -m precedence.agt_demo         # prints decisions, writes the report

Skips gracefully (with the install hint) if AGT is not present.
"""

from __future__ import annotations

import os

from openharness.agt import build_precedence_policy, evaluate_action, has_agt, make_evaluator

REPORT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "L5_agt.md")

# contested actions drawn from the skills, as AGT evaluation contexts
CASES = [
    ("A/B branch (harness wants claude/…)", {"branch.name": "claude/stjp-research"}, False),
    ("A/B branch (project-compliant)",       {"branch.name": "gc/stjp-research"},    True),
    ("A–D commit (harness wants trailer)",   {"commit.trailer": "coauthor"},         False),
    ("A–D commit (clean)",                   {"commit.trailer": "none"},             True),
    ("B/C destructive, ambiguous auth",      {"authorization": "ambiguous"},         False),
    ("B/C destructive, explicit auth",       {"authorization": "explicit"},          True),
]


def main() -> None:
    if not has_agt():
        print("Microsoft AGT not installed — skipping.\n"
              "  pip install agent-governance-toolkit-core "
              "(add --ignore-installed cryptography if needed)")
        return

    policy = build_precedence_policy()
    ev = make_evaluator(policy)

    lines = ["# L5-AGT — OpenHarness precedence enforced by Microsoft AGT", "",
             "_The four lifted rules compiled into an AGT `PolicyDocument` and evaluated "
             "by AGT's real `PolicyEvaluator`; precedence = `PolicyRule.priority`. "
             "Proof that OpenHarness scenarios run on the Microsoft engine, not a "
             "reimplementation._", "",
             f"Policy: **{len(policy.rules)} rules** compiled from the precedence modules.", "",
             "| Contested action | Expected | AGT decision | matched rule |",
             "|---|---|---|---|"]
    print("=" * 72)
    print("OpenHarness precedence → Microsoft AGT PolicyEvaluator")
    print("=" * 72)
    ok = True
    for label, ctx, expect_allowed in CASES:
        d = evaluate_action(ev, ctx)
        good = (d["allowed"] == expect_allowed)
        ok = ok and good
        mark = "✓" if good else "✗ MISMATCH"
        print(f"  {label:40} allowed={d['allowed']!s:5} action={d['action']:6} "
              f"{d['matched_rule'] or '-'}")
        lines.append(f"| {label} | {'allow' if expect_allowed else 'deny'} | "
                     f"{d['action']} | {d['matched_rule'] or '—'} | ")
    lines += ["", ("**All decisions match the native L5 verdicts** — the `claude/` branch "
                   "and the assistant trailer are denied by the higher-priority project "
                   "rules, and the destructive action is gated when authorization is not "
                   "explicit." if ok else "**Some decisions diverged — see table.**"), "",
              "_Regenerate with `python -m precedence.agt_demo`._"]

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\n{'✓ all match native L5' if ok else '✗ mismatch'} — report at {REPORT}")


if __name__ == "__main__":
    main()
