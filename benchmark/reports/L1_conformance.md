# L1 — Conformance-detection benchmark

**Corpus:** 38 labeled traces across 5 modules, including adversarial near-misses.
**Overall:** P=1.00 R=1.00 F1=1.00 acc=1.00  (TP20 FP0 FN0 TN18)

Positive class = *violation* (module returns FAIL). The deterministic/static modules are conformance checks by construction, so this measures whether each checker implements its spec — adversarial rows are where bugs would surface.

## Per module

| Module | Precision | Recall | F1 | Acc | TP/FP/FN/TN |
|---|---|---|---|---|---|
| `conventional-commits` (static) | 1.00 | 1.00 | 1.00 | 1.00 | 4/0/0/3 |
| `no-secrets` (static) | 1.00 | 1.00 | 1.00 | 1.00 | 3/0/0/3 |
| `pii-guard` (static) | 1.00 | 1.00 | 1.00 | 1.00 | 2/0/0/4 |
| `prose-style` (llm_judge) | 1.00 | 1.00 | 1.00 | 1.00 | 2/0/0/2 |
| `tdd` (deterministic) | 1.00 | 1.00 | 1.00 | 1.00 | 9/0/0/6 |

## Per task type

| Task type | Precision | Recall | F1 | Acc |
|---|---|---|---|---|
| bug_fix | 1.00 | 1.00 | 1.00 | 1.00 |
| data_analysis | 1.00 | 1.00 | 1.00 | 1.00 |
| docs | 1.00 | 1.00 | 1.00 | 1.00 |
| feature | 1.00 | 1.00 | 1.00 | 1.00 |
| refactor | 1.00 | 1.00 | 1.00 | 1.00 |

## Misclassifications

None — every labeled trace, including adversarial near-misses, was classified correctly.

_Regenerate with `python -m benchmark.l1_conformance`._
