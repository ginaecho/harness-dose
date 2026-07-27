---
name: hotfix
description: >-
  Branch a fix, commit it, and force-push to update an open PR. Use for urgent
  fixes to an existing pull request.
harness_modules: [branch-policy, no-assistant-trailer, confirm-destructive]
failure_classes: [C1, C2, C4]
emits_actions: [branch.create, commit.create, force.push]
---

# Hotfix

Ship the fix. Branch naming (C1) and commit-trailer (C2) are governed exactly as
in the research skill. The new rule here is `confirm-destructive`: a **force-push
is destructive** and requires *explicit prior authorization*. An ambiguous
go-ahead ("looks fine, right?") is not authorization — the deterministic gate
blocks the action rather than letting you resolve the ambiguity toward doing it.

## Steps

1. **Branch** the fix — `branch.create` (governed, C1).
2. **Commit** — `commit.create` (governed, C2).
3. **Force-push** — `force.push`. Gated by `confirm-destructive` (C4): no explicit
   authorization on record → the layer stops and reports instead of pushing.
