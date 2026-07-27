# L5 — Precedence & conflict ablation

_Synthetic scenario encoding a real incident: the four mistakes that came from ordering, not ignorance. It proves the **mechanism** — an ordered, externalized layer removes ordering/scope/discretion failures and makes conflicts explicit — not real-agent efficacy. See [evaluation-methodology.md](../../docs/evaluation-methodology.md)._

## Failure classes

- **C1** — branch name (contradiction)
- **C2** — commit trailer (contradiction)
- **C3** — reply scope (under-specified)
- **C4** — destructive auth (under-specified)

## Static conflict set (computed before any run, FORGE-style)

2 contradicting rule pairs found by static scan:

- `branch-policy` **forbid** *claude* on `branch.name`  ⟷  `harness-branch-default` **require** *claude*  (project vs harness)
- `no-assistant-trailer` **forbid** *coauthor* on `commit.trailer`  ⟷  `harness-commit-trailer` **require** *coauthor*  (project vs harness)

Note what is **absent**: the reply-scope (C3) and destructive-auth (C4) rules are not in the conflict set. They are under-specification, not contradiction — the static scan cannot catch them, which is exactly why precedence alone would not have saved items 3 and 4.

## Outcome per skill (✓ = clean, else the failure classes that fire)

| Skill | embedded | externalized, bad order | externalized, right order |
|---|---|---|---|
| A: research-writeup | C1, C2, C3 | C1, C2 | ✓ |
| B: hotfix | C1, C2, C4 | C1, C2 | ✓ |
| C: cleanup | C2, C4 | C2 | ✓ |
| D: docs-update | C2, C3 | C2 | ✓ |

| Condition | Skills fully clean |
|---|---|
| embedded | 0/4 |
| externalized, bad order | 0/4 |
| externalized, right order | 4/4 |

**Reading it:** externalizing with the *bad* order still fails C1/C2 — so the fix is the **ordering**, not the move itself. The right order clears C1/C2; declarative scope clears C3; the deterministic gate clears C4. Three failure classes, three distinct mechanisms.

## Observability: conflicts silent vs logged

The C1/C2 contradictions exist in every condition. Embedded resolved **6** of them **silently**; the externalized layer **logged 12** of them as verdicts across the two externalized conditions. Same contradictions — one condition hides them, the other puts them on the record.

## Which orderings generalize across A–D? (scope + gate held on)

| Source ordering (highest → lowest) | Contradiction failures |
|---|---|
| conversation > project > harness | 0 |
| project > conversation > harness | 0 |
| project > harness > conversation | 0 |
| conversation > harness > project | 6 |
| harness > conversation > project | 6 |
| harness > project > conversation | 6 |

Every ordering with **project above harness** clears all contradictions across the whole skill family; every ordering with harness on top fails. The winning order matches the record's conclusion: *explicit conversation > project rule files > harness defaults.*

_Regenerate with `python -m precedence.experiment`._
