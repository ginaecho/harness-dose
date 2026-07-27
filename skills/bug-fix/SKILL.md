---
name: bug-fix
description: >-
  Fix a reported bug in the codebase. Use when a defect, regression, or failing
  behavior needs a targeted code change. Produces a minimal fix backed by a test.
harness_module: tdd
lifted_rule: "Write the failing test before the code that passes it."
emits_events: [test.written, test.run, code.modified]
---

# Fixing a bug

A bug fix is a *task*. The discipline that makes it trustworthy — test-first —
is **not** written here as advice; it is enforced from above by the `tdd`
harness module, which binds to every `code.modified` event on this task and
verifies a failing test preceded it. Your job is the task; the layer holds the
reins on the how.

## Steps

1. **Reproduce.** Understand the defect from the report; find the smallest input
   that triggers it.
2. **Locate.** Trace to the responsible function. Keep the blast radius small.
3. **Fix.** Make the minimal change that resolves the defect. Emit
   `code.modified` for each file you touch.
4. **Verify.** Re-run the test suite; emit `test.run`.

## What the agent emits

An agent following this skill emits, per fix:

- `test.written` (name, status) — a new test capturing the defect
- `code.modified` (files, lines) — the fix
- `test.run` (status) — the suite result

The `tdd` module reads that stream and returns a verdict. You never decide
whether the rule applies — that is the layer's call, by design.
