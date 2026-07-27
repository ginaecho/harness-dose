"""L1 — does the layer MEASURE conformance correctly?

Run every module over the labeled corpus (including adversarial near-misses) and
score it as a violation classifier: precision, recall, F1, and a confusion
matrix, overall and per task type. Fully offline and deterministic.

Honesty note, stated in the report too: the deterministic/static modules are
conformance checks *by construction* — L1 is therefore a test of whether each
checker faithfully implements its spec (where implementation bugs show up on the
adversarial rows), not a test of a model. The one model-shaped module,
``prose-style``, ships a deterministic proxy judge; L1 measures proxy-vs-spec
consistency. Measuring the judge's agreement with *human* labels is a separate
step, and ``benchmark.agent_sim`` gives you the labeled interface to do it.
"""

from __future__ import annotations

import os
from collections import defaultdict

from openharness.harness import Harness
from openharness.module import Verdict
from modules import ALL
from .agent_sim import LabeledRun, corpus
from .metrics import Confusion

_MOD = {m.id: m for m in ALL}
REPORT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "L1_conformance.md")


def _predict_violating(run: LabeledRun) -> bool:
    """Run the module over the trace; predict 'violating' if it ever FAILs."""
    h = Harness([_MOD[run.module_id]], session_id="l1")
    h.run(run.events)
    return any(o.verdict == Verdict.FAIL for o in h.trace.for_module(run.module_id))


def evaluate() -> tuple[dict[str, Confusion], dict[str, Confusion], list[tuple[LabeledRun, bool]]]:
    per_module: dict[str, Confusion] = defaultdict(Confusion)
    per_tasktype: dict[str, Confusion] = defaultdict(Confusion)
    rows: list[tuple[LabeledRun, bool]] = []
    for run in corpus():
        pred = _predict_violating(run)
        per_module[run.module_id].add(truth_violating=run.truth_violating,
                                      predicted_violating=pred)
        per_tasktype[run.task_type].add(truth_violating=run.truth_violating,
                                        predicted_violating=pred)
        rows.append((run, pred))
    return dict(per_module), dict(per_tasktype), rows


def _md(per_module, per_tasktype, rows) -> str:
    overall = Confusion()
    for c in per_module.values():
        overall = overall.merge(c)
    misses = [(r, p) for r, p in rows if r.truth_violating != p]

    lines = ["# L1 — Conformance-detection benchmark", ""]
    lines.append(f"**Corpus:** {len(rows)} labeled traces across {len(per_module)} "
                 f"modules, including adversarial near-misses.")
    lines.append(f"**Overall:** {overall.row()}")
    lines.append("")
    lines.append("Positive class = *violation* (module returns FAIL). "
                 "The deterministic/static modules are conformance checks by "
                 "construction, so this measures whether each checker implements "
                 "its spec — adversarial rows are where bugs would surface.")
    lines.append("")
    lines.append("## Per module")
    lines.append("")
    lines.append("| Module | Precision | Recall | F1 | Acc | TP/FP/FN/TN |")
    lines.append("|---|---|---|---|---|---|")
    for mid in sorted(per_module):
        c = per_module[mid]
        tier = _MOD[mid].price.tier.value
        lines.append(f"| `{mid}` ({tier}) | {c.precision:.2f} | {c.recall:.2f} | "
                     f"{c.f1:.2f} | {c.accuracy:.2f} | {c.tp}/{c.fp}/{c.fn}/{c.tn} |")
    lines.append("")
    lines.append("## Per task type")
    lines.append("")
    lines.append("| Task type | Precision | Recall | F1 | Acc |")
    lines.append("|---|---|---|---|---|")
    for tt in sorted(per_tasktype):
        c = per_tasktype[tt]
        lines.append(f"| {tt} | {c.precision:.2f} | {c.recall:.2f} | {c.f1:.2f} | {c.accuracy:.2f} |")
    lines.append("")
    lines.append("## Misclassifications")
    lines.append("")
    if not misses:
        lines.append("None — every labeled trace, including adversarial near-misses, "
                     "was classified correctly.")
    else:
        lines.append("| Module | Variant | Truth | Predicted |")
        lines.append("|---|---|---|---|")
        for r, p in misses:
            lines.append(f"| `{r.module_id}` | {r.variant} | "
                         f"{'violating' if r.truth_violating else 'compliant'} | "
                         f"{'violating' if p else 'compliant'} |")
    lines.append("")
    lines.append("_Regenerate with `python -m benchmark.l1_conformance`._")
    return "\n".join(lines) + "\n"


def main() -> None:
    per_module, per_tasktype, rows = evaluate()
    overall = Confusion()
    for c in per_module.values():
        overall = overall.merge(c)

    print("=" * 72)
    print("L1 — Conformance-detection benchmark")
    print("=" * 72)
    print(f"corpus: {len(rows)} labeled traces (incl. adversarial near-misses)\n")
    for mid in sorted(per_module):
        print(f"  {mid:22} {per_module[mid].row()}")
    print(f"\n  {'OVERALL':22} {overall.row()}")
    misses = [(r, p) for r, p in rows if r.truth_violating != p]
    if misses:
        print(f"\n  {len(misses)} misclassification(s):")
        for r, p in misses:
            print(f"    - {r.module_id}: {r.variant} "
                  f"(truth={'viol' if r.truth_violating else 'ok'}, "
                  f"pred={'viol' if p else 'ok'})")

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w") as f:
        f.write(_md(per_module, per_tasktype, rows))
    print(f"\n✓ report written to {REPORT}")


if __name__ == "__main__":
    main()
