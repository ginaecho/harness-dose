# L2 — Enforcement ablation (gating vs off)

**Setup:** 8 tasks × 30 seeds, p(violate)=0.5, max retries=2. Identical seeded decisions in both arms, so the delta is the harness.

| Metric | Harness off | Harness gating |
|---|---|---|
| Residual violation rate (final output) | **50%** | **0%** ± 0% |
| Task-success rate | 100% | 100% |
| Retries (enforcement overhead) / session | 0 | 4.0 ± 1.4 |
| Tokens spent on checks / session | 1200 | 1800 |

**Headline:** gating removes essentially all violations from the final output (50% → 0%) **without lowering task success** (100%). The cost is 4.0 retries per session — the displayed price of enforcement.

## What gating caught, by module (summed over seeds)

| Module | Violations caught & repaired |
|---|---|
| `conventional-commits` | 15 |
| `no-secrets` | 18 |
| `pii-guard` | 31 |
| `prose-style` | 15 |
| `tdd` | 40 |

## Friction signal: `tdd` on `prototype`

Of the retries, 15 came from forcing test-first on **prototype** tasks — where the `tdd` card scores low on purpose. The ablation *measures* that friction instead of asserting it: this is the quantitative basis for 'know when NOT to use a module'.

_Regenerate with `python -m benchmark.l2_ablation`._
