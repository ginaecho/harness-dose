"""Adapter: run OpenHarness governance on Microsoft's Agent Governance Toolkit.

OpenHarness and AGT are complementary. AGT (github.com/microsoft/agent-governance
-toolkit, MIT) is a production **enforcement** engine: a fail-closed policy gate
that intercepts tool calls, with YAML/OPA/Cedar policies, priority-based conflict
resolution, and tamper-evident audit. OpenHarness is the **characterization /
evaluation** layer above it: harness cards, the L1–L5 proofs, and the precedence
study.

They line up almost one-to-one, so OpenHarness can *compile down to AGT* and let
the real engine enforce:

| OpenHarness            | AGT (`agent_os.policies`)                 |
|------------------------|-------------------------------------------|
| `Source` ordering      | `PolicyRule.priority` + `PRIORITY_FIRST_MATCH` |
| `Directive` (REQUIRE/FORBID) | `PolicyRule` + `PolicyCondition` + `PolicyAction` |
| the layer's binding    | `PolicyEvaluator.evaluate(context)`       |
| the watcher's log      | `PolicyDecision.audit_entry`              |
| static conflict scan   | AGT `agt lint-policy` / `constraint_graph`|

AGT is an optional dependency. Install it with::

    pip install agent-governance-toolkit-core
    # if the base image ships an OS-managed `cryptography`, add:
    #   --ignore-installed cryptography

Everything here degrades gracefully when AGT is absent (see :func:`has_agt`).
"""

from __future__ import annotations

import warnings
from typing import Any

from openharness.govern import Polarity, Source

# Source precedence → AGT integer priority (higher wins under PRIORITY_FIRST_MATCH).
SOURCE_PRIORITY = {
    Source.CONVERSATION: 300,
    Source.PROJECT: 200,
    Source.HARNESS: 100,
}


def has_agt() -> bool:
    """True iff Microsoft AGT's policy engine is importable."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import agent_os.policies  # noqa: F401
        return True
    except Exception:
        return False


def _require_agt():
    if not has_agt():
        raise ImportError(
            "Microsoft AGT is not installed. Install it with "
            "`pip install agent-governance-toolkit-core` "
            "(add `--ignore-installed cryptography` if the base image ships one).")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import agent_os.policies as P
    return P


def build_precedence_policy(modules=None):
    """Compile OpenHarness precedence modules into an AGT ``PolicyDocument``.

    Mapping:
    * a ``FORBID`` directive → a ``DENY`` rule at the source's priority;
    * a harness-default ``REQUIRE`` (it *wants* the value) → an ``ALLOW`` rule at
      the (lower) harness priority — so the project ``DENY`` wins by precedence;
    * ``confirm-destructive`` (REQUIRE authorization == explicit) → a ``DENY`` when
      the authorization is anything but ``explicit`` (the deterministic gate).

    Scope-only rules (e.g. reply governance) are not policy conditions; AGT
    expresses those via ``PolicyScope`` / tool allowlists instead.
    """
    P = _require_agt()
    if modules is None:
        from precedence.rules import ALL_MODULES
        modules = ALL_MODULES

    rules = []
    for m in modules:
        for d in m.directives:
            pri = SOURCE_PRIORITY.get(d.source, 0)
            if d.target == "authorization":  # the destructive gate
                cond = P.PolicyCondition(field="authorization",
                                         operator=P.PolicyOperator.NE, value="explicit")
                rules.append(P.PolicyRule(name=f"{m.id}", condition=cond,
                                          action=P.PolicyAction.DENY, priority=pri,
                                          message=d.message))
                continue
            if d.value.startswith("^"):
                continue  # positive-format requirement; handled by AGT scope, not shown here
            action = P.PolicyAction.DENY if d.polarity == Polarity.FORBID else P.PolicyAction.ALLOW
            cond = P.PolicyCondition(field=d.target, operator=P.PolicyOperator.CONTAINS,
                                     value=d.value)
            rules.append(P.PolicyRule(name=f"{m.id}/{d.target}", condition=cond,
                                      action=action, priority=pri, message=d.message))

    return P.PolicyDocument(name="openharness-precedence", rules=rules)


def make_evaluator(policy=None):
    """Return an AGT ``PolicyEvaluator`` for the precedence policy."""
    P = _require_agt()
    doc = policy if policy is not None else build_precedence_policy()
    return P.PolicyEvaluator(policies=[doc])


def evaluate_action(evaluator, context: dict[str, Any]) -> dict[str, Any]:
    """Run one action's context through AGT; return a plain-dict decision."""
    d = evaluator.evaluate(context)
    return {"allowed": d.allowed, "action": str(d.action),
            "matched_rule": d.matched_rule, "reason": d.reason}
