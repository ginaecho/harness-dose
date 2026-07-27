---
name: data-query
description: >-
  Answer a question about the data by writing and running a SQL query. Use for
  analytics, reporting, and ad-hoc data pulls. Produces a query and a finding.
harness_module: pii-guard
lifted_rule: "Any query touching a PII column must mask, hash, or carry approved access."
emits_events: [query.executed, doc.written]
---

# Answering a data question

Write the SQL that answers the question and report the finding. The rule that
keeps this safe — never let unmasked PII leave a query — is **not** restated
here; it is enforced by the `pii-guard` module, which binds to every
`query.executed` event whose SQL references a PII column and fails it unless the
column is masked, hashed, or the query carries an approved-access marker.

## Steps

1. **Frame.** Turn the question into a precise, answerable query.
2. **Write SQL.** Prefer aggregates over row-level PII. When you must reference a
   PII column (`email`, `ssn`, `phone`, `dob`, `address`, `credit_card`), wrap it
   in `hash(...)` / `mask(...)`. Emit `query.executed` (sql).
3. **Report.** Summarize the finding plainly. Emit `doc.written` (content).

## What the agent emits

- `query.executed` (sql) — the query it ran
- `doc.written` (content) — the finding

`pii-guard` (a static-tier check, critical severity) parses the SQL and verdicts
it. The masking decision is verified from outside — the agent cannot wave it
through.
