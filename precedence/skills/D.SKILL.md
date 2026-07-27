---
name: docs-update
description: >-
  Update documentation, commit it, and reply to the user with a summary of what
  changed. Use for docs-only changes.
harness_modules: [no-assistant-trailer, reply-scope]
failure_classes: [C2, C3]
emits_actions: [commit.create, reply.write]
---

# Docs update

Update the docs. This skill has no branch or destructive step, but it still
shares two rules with the family: the commit-trailer rule (C2) and the
reply-governance rule (C3, §5 governs the reply, not only the document). Sharing
the *same* modules across skills with different goals is the point — one harness
layer, characterized once, reused everywhere.

## Steps

1. **Commit** the docs change — `commit.create` (governed, C2).
2. **Reply** with a summary — `reply.write`. `reply-scope` (C3) applies here by
   declared scope; it cannot be narrowed to "documents only".
