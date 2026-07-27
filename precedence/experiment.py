"""L5 — the precedence / conflict ablation.

Runs skills A–D under three conditions and reports, per skill, which of the four
failure classes occur:

* **embedded**              — rules in skill prose; agent resolves by the bad
  order (harness > conversation > project), scopes by discretion, proceeds on
  ambiguous authorization. (What actually happened.)
* **externalized, bad order** — rules re-mounted as a layer, but precedence still
  wrong. Fixes the *scope* and *authorization* failures (declarative scope +
  deterministic gate) but **not** the contradictions — proving externalizing is
  not the fix; the ordering is.
* **externalized, right order** — layer with the correct precedence
  (conversation > project > harness). All four fixed.

Also emits the FORGE-style static conflict set (computed before any run) and a
sweep over every source ordering to find which generalize across the skills.
"""

from __future__ import annotations

import itertools
import os
from dataclasses import dataclass

from openharness.govern import (AuditEntry, Directive, Polarity, Source,
                                resolve_by_precedence, static_conflicts)
from .rules import all_directives
from .scenarios import SKILLS, Action

REPORT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "L5_precedence.md")

BAD_ORDER = (Source.HARNESS, Source.CONVERSATION, Source.PROJECT)
RIGHT_ORDER = (Source.CONVERSATION, Source.PROJECT, Source.HARNESS)

FAILURE_LABEL = {
    "C1": "branch name (contradiction)",
    "C2": "commit trailer (contradiction)",
    "C3": "reply scope (under-specified)",
    "C4": "destructive auth (under-specified)",
}


@dataclass(frozen=True)
class Condition:
    name: str
    precedence: tuple
    declarative_scope: bool
    gate: bool
    logs_conflicts: bool


CONDITIONS = [
    Condition("embedded", BAD_ORDER, declarative_scope=False, gate=False, logs_conflicts=False),
    Condition("externalized, bad order", BAD_ORDER, declarative_scope=True, gate=True, logs_conflicts=True),
    Condition("externalized, right order", RIGHT_ORDER, declarative_scope=True, gate=True, logs_conflicts=True),
]


def _resolve_contested(action: Action, precedence: tuple) -> str:
    directives = [Directive(src.value, src, "attr", Polarity.REQUIRE, val)
                  for src, val in action.candidates.items()]
    winner = resolve_by_precedence(directives, precedence)
    return winner.value if winner else ""


def violates(action: Action, cond: Condition) -> bool:
    fc = action.failure_class
    if fc in ("C1", "C2"):
        return _resolve_contested(action, cond.precedence) != action.correct
    if fc == "C3":
        return not cond.declarative_scope          # scope, not precedence
    if fc == "C4":
        return (not cond.gate) and (not action.auth_present)  # gate, not precedence
    return False


def run():
    # per skill, per condition -> list of failing classes
    grid: dict[tuple[str, str], list[str]] = {}
    silent = logged = 0
    for skill in SKILLS:
        for cond in CONDITIONS:
            fails = [a.failure_class for a in skill.actions if violates(a, cond)]
            grid[(skill.name, cond.name)] = fails
            # count conflicts (C1/C2 have a real contradiction) as silent vs logged
            conflicts = sum(1 for a in skill.actions if a.failure_class in ("C1", "C2"))
            if cond.name == "embedded":
                silent += conflicts
            elif cond.logs_conflicts:
                logged += conflicts
    return grid, silent, logged


def precedence_sweep():
    """For scope+gate on, sweep every source ordering; rank by total contradictions."""
    on = Condition("sweep", (), True, True, True)
    results = []
    for perm in itertools.permutations([Source.CONVERSATION, Source.PROJECT, Source.HARNESS]):
        c = Condition("sweep", perm, True, True, True)
        total = sum(1 for skill in SKILLS for a in skill.actions
                    if a.failure_class in ("C1", "C2") and violates(a, c))
        results.append((perm, total))
    return sorted(results, key=lambda x: x[1])


def audit(skill, cond: Condition) -> list[AuditEntry]:
    """Watcher view: per action, the resolved winner, conflict, and compliance."""
    from .rules import ALL_MODULES
    entries = []
    for a in skill.actions:
        in_scope = [m for m in ALL_MODULES if a.type in m.scope]
        directives = [d for m in in_scope for d in m.directives]
        conflict = len(static_conflicts(directives)) > 0
        winner = None
        if a.candidates:
            winner = resolve_by_precedence(
                [Directive(s.value, s, "attr", Polarity.REQUIRE, v) for s, v in a.candidates.items()],
                cond.precedence)
        complied = not violates(a, cond)
        entries.append(AuditEntry(
            action_type=a.type, target=a.failure_class, in_scope=directives,
            winner=winner, conflict=conflict,
            silently_resolved=conflict and not cond.logs_conflicts,
            complied=complied,
            detail=FAILURE_LABEL.get(a.failure_class, "")))
    return entries


def _md(grid, silent, logged, conflicts, sweep) -> str:
    L = ["# L5 — Precedence & conflict ablation", "",
         "_Synthetic scenario encoding a real incident: the four mistakes that came "
         "from ordering, not ignorance. It proves the **mechanism** — an ordered, "
         "externalized layer removes ordering/scope/discretion failures and makes "
         "conflicts explicit — not real-agent efficacy. See "
         "[evaluation-methodology.md](../../docs/evaluation-methodology.md)._", ""]

    L.append("## Failure classes")
    L.append("")
    for k, v in FAILURE_LABEL.items():
        L.append(f"- **{k}** — {v}")
    L.append("")

    L.append("## Static conflict set (computed before any run, FORGE-style)")
    L.append("")
    L.append(f"{len(conflicts)} contradicting rule pairs found by static scan:")
    L.append("")
    for a, b in conflicts:
        L.append(f"- `{a.module_id}` **{a.polarity.value}** *{a.value}* on `{a.target}`  ⟷  "
                 f"`{b.module_id}` **{b.polarity.value}** *{b.value}*  "
                 f"({a.source.value} vs {b.source.value})")
    L.append("")
    L.append("Note what is **absent**: the reply-scope (C3) and destructive-auth (C4) "
             "rules are not in the conflict set. They are under-specification, not "
             "contradiction — the static scan cannot catch them, which is exactly why "
             "precedence alone would not have saved items 3 and 4.")
    L.append("")

    L.append("## Outcome per skill (✓ = clean, else the failure classes that fire)")
    L.append("")
    header = "| Skill | " + " | ".join(c.name for c in CONDITIONS) + " |"
    L.append(header)
    L.append("|" + "---|" * (len(CONDITIONS) + 1))
    for skill in SKILLS:
        cells = []
        for cond in CONDITIONS:
            fails = grid[(skill.name, cond.name)]
            cells.append("✓" if not fails else ", ".join(sorted(set(fails))))
        L.append(f"| {skill.name} | " + " | ".join(cells) + " |")
    L.append("")

    # success rates
    L.append("| Condition | Skills fully clean |")
    L.append("|---|---|")
    for cond in CONDITIONS:
        clean = sum(1 for skill in SKILLS if not grid[(skill.name, cond.name)])
        L.append(f"| {cond.name} | {clean}/{len(SKILLS)} |")
    L.append("")

    L.append("**Reading it:** externalizing with the *bad* order still fails C1/C2 — "
             "so the fix is the **ordering**, not the move itself. The right order "
             "clears C1/C2; declarative scope clears C3; the deterministic gate "
             "clears C4. Three failure classes, three distinct mechanisms.")
    L.append("")

    L.append("## Observability: conflicts silent vs logged")
    L.append("")
    L.append(f"The C1/C2 contradictions exist in every condition. Embedded resolved "
             f"**{silent}** of them **silently**; the externalized layer **logged "
             f"{logged}** of them as verdicts across the two externalized conditions. "
             f"Same contradictions — one condition hides them, the other puts them on "
             f"the record.")
    L.append("")

    L.append("## Which orderings generalize across A–D? (scope + gate held on)")
    L.append("")
    L.append("| Source ordering (highest → lowest) | Contradiction failures |")
    L.append("|---|---|")
    for perm, total in sweep:
        L.append("| " + " > ".join(s.value for s in perm) + f" | {total} |")
    L.append("")
    L.append("Every ordering with **project above harness** clears all contradictions "
             "across the whole skill family; every ordering with harness on top fails. "
             "The winning order matches the record's conclusion: "
             "*explicit conversation > project rule files > harness defaults.*")
    L.append("")
    L.append("_Regenerate with `python -m precedence.experiment`._")
    return "\n".join(L) + "\n"


def main() -> None:
    grid, silent, logged = run()
    conflicts = static_conflicts(all_directives())
    sweep = precedence_sweep()

    print("=" * 74)
    print("L5 — Precedence & conflict ablation")
    print("=" * 74)
    print(f"\nStatic conflict set (before any run): {len(conflicts)} contradicting pairs")
    for a, b in conflicts:
        print(f"  - {a.module_id} {a.polarity.value} '{a.value}'  ⟷  "
              f"{b.module_id} {b.polarity.value} '{b.value}'")
    print("\nOutcome per skill:")
    print(f"  {'skill':22} " + " ".join(f"{c.name[:16]:16}" for c in CONDITIONS))
    for skill in SKILLS:
        row = []
        for cond in CONDITIONS:
            fails = grid[(skill.name, cond.name)]
            row.append(f"{('✓' if not fails else ','.join(sorted(set(fails)))):16}")
        print(f"  {skill.name:22} " + " ".join(row))
    for cond in CONDITIONS:
        clean = sum(1 for skill in SKILLS if not grid[(skill.name, cond.name)])
        print(f"    {cond.name:26} clean {clean}/{len(SKILLS)}")
    print(f"\nconflicts silently resolved (embedded): {silent}   logged (externalized): {logged}")
    print("\nBest orderings (0 contradiction failures):")
    for perm, total in sweep:
        if total == 0:
            print("  " + " > ".join(s.value for s in perm))

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w") as f:
        f.write(_md(grid, silent, logged, conflicts, sweep))
    print(f"\n✓ report written to {REPORT}")


if __name__ == "__main__":
    main()
