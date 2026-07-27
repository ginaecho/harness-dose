# The A–D skill family — four goals, one shared set of rules

These four skills have *different goals* but must all obey the *same four
governance rules*. That is the setup that makes ordering matter: the rules come
from different sources (project files, harness/session config, the live
conversation), and when two are in scope at once they can contradict.

| Skill | Goal | Actions | Failure classes in play |
|-------|------|---------|-------------------------|
| [A: research-writeup](A.SKILL.md) | branch → write → commit → reply | branch.create, commit.create, reply.write | C1, C2, C3 |
| [B: hotfix](B.SKILL.md) | branch → commit → force-push | branch.create, commit.create, force.push | C1, C2, C4 |
| [C: cleanup](C.SKILL.md) | delete artifacts → commit | file.delete, commit.create | C4, C2 |
| [D: docs-update](D.SKILL.md) | commit → reply | commit.create, reply.write | C2, C3 |

The four rules, and the mechanism that fixes each failure:

| # | Rule (lifted to a module) | Failure if mishandled | Fixed by |
|---|---------------------------|-----------------------|----------|
| C1 | `branch-policy` — `gc/` prefix, no "claude" | wrong branch name | **precedence** (project > harness) |
| C2 | `no-assistant-trailer` — no Co-Authored-By | forbidden trailer committed | **precedence** |
| C3 | `reply-scope` — §5 governs replies | generic guidance applied to replies | **declarative scope** |
| C4 | `confirm-destructive` — explicit auth first | destructive act on ambiguous "ok" | **deterministic gate** |

C1 and C2 are *contradictions* (two sources demand opposite things) → a static
scan catches them before running, and the right precedence resolves them. C3 and
C4 are *under-specification* → invisible to the static scan, and precedence does
not help; they need scope and gating instead. The experiment in
[`../experiment.py`](../experiment.py) shows all of this on the four skills.
