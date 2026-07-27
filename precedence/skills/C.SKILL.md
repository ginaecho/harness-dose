---
name: cleanup
description: >-
  Delete stale build artifacts and commit the removal. Use to reclaim space or
  remove generated files that should not be tracked.
harness_modules: [confirm-destructive, no-assistant-trailer]
failure_classes: [C4, C2]
emits_actions: [file.delete, commit.create]
---

# Cleanup

Remove the stale artifacts. `file.delete` is **destructive** — the single most
dangerous class of action, and the one where "can be deleted, right?" was read as
authorization and then extended into a filesystem sweep. `confirm-destructive`
(C4) gates every delete on explicit prior authorization; the commit that records
the removal is governed by `no-assistant-trailer` (C2).

## Steps

1. **Delete** each artifact — `file.delete`. Gated (C4): without explicit auth,
   the layer refuses and reports, with the exact list it would remove.
2. **Commit** the removal — `commit.create` (governed, C2).
