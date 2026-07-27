# Precedence, conflict, and the failures that come from ordering

Most of OpenHarness measures rules one at a time: *was this rule followed?* But
the failures that actually cause damage rarely come from a missing rule — they
come from **two rules in scope at once, resolved in the wrong order.** The agent
does the wrong thing *while dutifully following a rule*. This is the layer's real
job: to hold precedence from outside, make conflicts explicit, and remove the
agent's discretion to resolve ambiguity toward action.

## The incident this reproduces

A real session produced four mistakes that "came from ordering, not ignorance":

| # | Conflict | Nature |
|---|----------|--------|
| 1 | session config mandated a `claude/…` branch; AGENT.md forbids "claude" and requires `gc/` | **contradiction** |
| 2 | session config mandated a `Co-Authored-By: Claude` trailer; AGENT.md forbids assistant/session trailers | **contradiction** |
| 3 | AGENT.md §5 governs chat replies; generic system guidance was applied to replies instead | **scope** (under-specified) |
| 4 | "can be deleted, right?" was read as authorization; a confirm-first rule was overridden, then extended into a sweep | **authorization** (under-specified) |

The ordering that was *applied*: `harness defaults > recent literal words >
unread project files`. The ordering that would have been *right*: `explicit
conversation > project rule files > harness defaults`.

The key observation from the record: **precedence fixes contradiction; it does
not fix under-specification.** Items 1–2 are contradictions and a precedence rule
resolves them. Items 3–4 are not contradictions at all — no rule opposed them;
they were mis-scoped or resolved toward action under ambiguity. A precedence
order would not have caught them.

## What OpenHarness does about it

Three mechanisms, one per failure nature — implemented in
[`openharness/govern.py`](../openharness/govern.py) and demonstrated in
[`precedence/`](../precedence):

1. **Explicit precedence** (fixes 1, 2). Rules carry their **source**
   (`conversation` / `project` / `harness`), and the layer resolves contested
   properties by a declared order — not by the agent's in-the-moment guess.
2. **Declarative scope** (fixes 3). A module states which action types it binds
   to. `reply-scope` binds to `reply.write`; it cannot be quietly narrowed to
   "documents only."
3. **Deterministic gate** (fixes 4). A destructive action without explicit
   authorization is *blocked and reported* — the layer removes the agent's
   discretion to interpret an ambiguous "ok" as a go-ahead.

Plus a fourth, static, pre-run check:

4. **Conflict set** — [`static_conflicts()`](../openharness/govern.py) runs a
   FORGE-style (arXiv:2602.16708) scan over the directive set and returns the
   pairs that cannot both hold, *before anything executes.* In this scenario it
   returns exactly the two contradictions (branch name, commit trailer) — and,
   tellingly, **not** the reply-scope or destructive-auth rules, because those
   are under-specification, not contradiction. The scan's blind spot *is* the
   proof that precedence + static analysis are necessary but not sufficient.

## The experiment (L5)

`python -m precedence.experiment` runs four skills — A: research-writeup,
B: hotfix, C: cleanup, D: docs-update — that share the same four rules but pursue
different goals, under three conditions:

| Skill | embedded | externalized, **bad** order | externalized, **right** order |
|-------|----------|-----------------------------|-------------------------------|
| A: research-writeup | C1, C2, C3 | C1, C2 | ✓ |
| B: hotfix | C1, C2, C4 | C1, C2 | ✓ |
| C: cleanup | C2, C4 | C2 | ✓ |
| D: docs-update | C2, C3 | C2 | ✓ |
| **clean** | **0/4** | **0/4** | **4/4** |

Two results matter:

- **Externalizing is not the fix — the ordering is.** The middle column moves the
  rules into the layer but keeps the wrong precedence; scope and gating clear
  C3/C4, but the contradictions C1/C2 survive. Only the right order clears them.
- **Each failure class has its own mechanism.** Precedence → C1/C2; declarative
  scope → C3; deterministic gate → C4. One knob does not fix all four, and the
  report says which fixes which.

A precedence **sweep** over all six source orderings (scope + gate held on) shows
every ordering with *project above harness* clears the contradictions across the
whole family, and every ordering with *harness on top* fails — the same
conclusion the incident record reached, now measured across four skills instead
of asserted from one.

## The watcher — observing actions, not just replies

Verification follows the Microsoft agent-governance style: a **watcher / policy
engine observes the agent's inputs and its action stream** (branch created,
commit written, file deleted — not only the final reply). For each action the
watcher records which rules were in scope, which won by precedence, whether a
contradiction existed, and whether it was resolved **silently or logged**. In
this scenario the same contradictions are resolved **6 times silently** under the
embedded condition and **logged 12 times** under the externalized conditions —
identical conflicts, but one setup hides them and the other puts every one on the
record. That difference — from invisible influence to a stream of verdicts — is
the entire pitch of OpenHarness, now shown on the failure mode that actually
hurt.

## Honesty (per the methodology)

This is a **synthetic** scenario that encodes a real incident and a real taxonomy.
It proves the **mechanism** — an ordered, externalized layer removes
ordering/scope/discretion failures and makes conflicts explicit and statically
detectable. It does **not** prove real-agent efficacy; that requires running a
live agent under the two regimes and grading its action stream, which is the
natural next step (see [`evaluation-methodology.md`](evaluation-methodology.md),
Q5).
