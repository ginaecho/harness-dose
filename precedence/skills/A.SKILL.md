---
name: research-writeup
description: >-
  Open a branch, write a related-works section, commit it, and reply to the user
  with a summary. Use for research/writing tasks that end in a committed artifact
  and a chat reply.
harness_modules: [branch-policy, no-assistant-trailer, reply-scope]
failure_classes: [C1, C2, C3]
emits_actions: [branch.create, commit.create, reply.write]
---

# Research write-up

Do the research task. The three governance rules this skill once carried in its
prose — branch naming, commit-trailer hygiene, and which rule set governs your
*reply* — are **lifted out** into the harness layer. That layer decides them by
declared precedence and scope, not by your reading of the moment.

## Steps

1. **Branch.** Emit `branch.create`. The name is governed by `branch-policy`
   (project) — which *contradicts* the harness/session default that mandates a
   `claude/…` branch. The layer, not you, resolves that contradiction.
2. **Write** the related-works section.
3. **Commit.** Emit `commit.create`. `no-assistant-trailer` (project) forbids a
   `Co-Authored-By` / session trailer — which *contradicts* the harness default
   that mandates one.
4. **Reply.** Emit `reply.write`. `reply-scope` (project §5) governs replies, not
   just documents — the scope is declared, so it cannot be quietly narrowed.

This is the skill where items 1–3 of the incident happened. With the rules
embedded and resolved by the wrong order, all three fired.
