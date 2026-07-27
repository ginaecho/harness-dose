# L5-AGT — OpenHarness precedence enforced by Microsoft AGT

_The four lifted rules compiled into an AGT `PolicyDocument` and evaluated by AGT's real `PolicyEvaluator`; precedence = `PolicyRule.priority`. Proof that OpenHarness scenarios run on the Microsoft engine, not a reimplementation._

Policy: **6 rules** compiled from the precedence modules.

| Contested action | Expected | AGT decision | matched rule |
|---|---|---|---|
| A/B branch (harness wants claude/…) | deny | deny | branch-policy/branch.name | 
| A/B branch (project-compliant) | allow | allow | — | 
| A–D commit (harness wants trailer) | deny | deny | no-assistant-trailer/commit.trailer | 
| A–D commit (clean) | allow | allow | — | 
| B/C destructive, ambiguous auth | deny | deny | confirm-destructive | 
| B/C destructive, explicit auth | allow | allow | — | 

**All decisions match the native L5 verdicts** — the `claude/` branch and the assistant trailer are denied by the higher-priority project rules, and the destructive action is gated when authorization is not explicit.

_Regenerate with `python -m precedence.agt_demo`._
