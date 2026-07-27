---
name: commit-changes
description: >-
  Commit completed work to version control with a clear, structured message.
  Use after a change is ready to record. Produces one or more commits.
harness_module: conventional-commits
lifted_rule: "Commit subjects must be `type(scope): summary`, ≤ 72 chars."
emits_events: [commit.created]
---

# Committing changes

Record the work as a commit. The message convention is **not** documented here
as a style preference; it is enforced by the `conventional-commits` module,
which binds to every `commit.created` event and verdicts the subject line
against the Conventional Commits grammar.

## Steps

1. **Stage** the related change as one logical unit.
2. **Write the subject** as `type(scope): summary` — `type` ∈ {feat, fix, docs,
   refactor, perf, test, build, ci, chore, revert}; `scope` optional; summary in
   the imperative, ≤ 72 chars. Emit `commit.created` (message).
3. **Body** (optional): explain *why*, not *what*.

## What the agent emits

- `commit.created` (message) — the full commit message

`conventional-commits` (static tier, minor severity) matches the subject and
returns pass/fail with the subject as evidence.
