# Building on Microsoft's Agent Governance Toolkit (AGT)

OpenHarness is a Microsoft hackathon project, and it composes with Microsoft's
[Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit)
(AGT, MIT) rather than competing with it. This is not aspirational: the four
lifted rules of the precedence study compile into an AGT `PolicyDocument` and are
enforced by AGT's real `PolicyEvaluator` — see [`precedence/agt_demo.py`](../precedence/agt_demo.py)
and [`openharness/agt.py`](../openharness/agt.py).

## The division of labour

**AGT enforces. OpenHarness characterizes and proves.**

- **AGT** is a production *enforcement* engine: a fail-closed gate that intercepts
  tool calls before they execute, with YAML/OPA/Cedar policies, **priority-based
  conflict resolution**, tamper-evident audit, `agt lint-policy`, and SDKs for
  Python/TS/.NET/Rust/Go. It answers: *may this action run?*
- **OpenHarness** is the *characterization and evaluation* layer above it: harness
  **cards** (competence per task type, cost, momentum), the **L1–L5 proofs**, and
  the **precedence study**. It answers: *which rule is good at what, is it being
  followed, what does it cost, and does externalizing/ordering it actually help?*

AGT tells you whether an action is allowed. OpenHarness tells you which harness to
reach for, and proves it — a *materia medica* on top of AGT's policy engine.

## They line up almost one-to-one

| OpenHarness concept | AGT (`agent_os.policies`) |
|---------------------|---------------------------|
| `Source` precedence ordering | `PolicyRule.priority` + `ConflictResolutionStrategy.PRIORITY_FIRST_MATCH` |
| `Directive` (REQUIRE / FORBID) | `PolicyRule` + `PolicyCondition` + `PolicyAction` (ALLOW/DENY/BLOCK) |
| the layer's binding decision | `PolicyEvaluator.evaluate(context) → PolicyDecision` |
| the watcher's verdict log | `PolicyDecision.audit_entry` (tamper-evident audit) |
| L5 static conflict scan | AGT `agt lint-policy` / `agent_os.constraint_graph` |
| harness cards, L1–L5 | *(no AGT equivalent — this is what OpenHarness adds)* |

## It runs — verified in-container

`pip install agent-governance-toolkit-core` pulls AGT 4.1.0 and its deps from
PyPI. Compiling the precedence modules and evaluating the contested actions
yields, on AGT's own engine:

```
A/B branch (harness wants claude/…)   allowed=False  action=deny   branch-policy/branch.name
A/B branch (project-compliant)        allowed=True   action=allow  -
A–D commit (harness wants trailer)    allowed=False  action=deny   no-assistant-trailer/commit.trailer
A–D commit (clean)                    allowed=True   action=allow  -
B/C destructive, ambiguous auth       allowed=False  action=deny   confirm-destructive
B/C destructive, explicit auth        allowed=True   action=allow  -
```

Every decision matches the native L5 verdicts: the `claude/` branch and the
assistant trailer are denied because the project rules carry higher `priority`
than the harness defaults, and the destructive action is gated when authorization
is not explicit. Regenerate with `make agt` (`python -m precedence.agt_demo`).

## Install

```bash
pip install agent-governance-toolkit-core
# If the base image ships an OS-managed `cryptography` that pip cannot replace:
pip install --ignore-installed cryptography agent-governance-toolkit-core
```

The dependency is **optional**. `openharness/agt.py` degrades gracefully
(`has_agt()`), and the AGT tests skip when it is absent, so OpenHarness runs with
or without AGT installed.

## The hackathon pitch, in one line

> Microsoft AGT makes unsafe actions *structurally impossible*. OpenHarness makes
> the governance itself *observable, testable, and comparable* — harness cards and
> an evaluation methodology (L1–L5, including the precedence/ordering study) that
> sit on top of AGT's engine.

## What we take from AGT even where we don't call it

Two AGT primitives validated the OpenHarness design and are worth adopting
directly: **priority-based conflict resolution** (which is exactly the L5
precedence mechanism, already production-grade in AGT) and **policy linting /
constraint graphs** (which generalize the L5 static conflict scan). Where AGT
already does it better, OpenHarness compiles down to AGT; where AGT has no
equivalent — the cards and the proofs — OpenHarness is the addition.
