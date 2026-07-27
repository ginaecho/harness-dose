# Evaluation methodology — how (and how *not*) to prove a harness works

> The hard core of OpenHarness is not the plumbing. It is the claim that a
> harness module can be *evaluated*. This document is deliberately skeptical
> about that claim, including about our own benchmarks. It states, for each
> thing we measure, exactly what the measurement proves and what it does **not**,
> and marks every dataset as **synthetic** or **real**.

## The circularity problem, stated plainly

A harness module is (in part) a *checker*: a classifier that reads a trace and
says "rule followed" or "violated." To score a classifier you need a labeled
test set — a golden dataset. But if the **same author**, in the **same effort**,
writes both the checker and the labels, the test can degenerate into the checker
grading its own homework. The failure mode is precise:

- **Legitimate:** label each example from the rule's **intent / specification**
  ("a query that leaks `ssn` unmasked *must* fail — that is what the rule is
  *for*"), written down independently of the code, ideally *before* the checker,
  and frozen.
- **Cheating:** label each example by **running the checker** and recording its
  output. Now the "test" only asserts the checker equals itself. It can never
  fail, and it proves nothing.

Writing the golden set *while* building the harness is fine — encouraged, even
(it is just test-driven development applied to the harness). The line that must
not be crossed is the source of the labels: **intent or an independent oracle,
never the tool under test.**

## "Evaluate a harness" is six questions, not one

Treating it as a single question is what makes it feel impossible. Each
sub-question has a different valid method, a different data source, and a
different exposure to circularity.

| # | Question | Method | Ground truth from | Circularity risk |
|---|----------|--------|-------------------|------------------|
| 1 | Does the checker implement its spec? (**implementation**) | property + mutation tests, adversarial fixtures | rule intent, spec-first | **high** if labeled from the checker |
| 2 | Does it bind on the right events? (**scope**) | precision/recall of *binding* | labeled event stream | medium |
| 3 | Does the rule catch real violations? (**coverage / validity**) | real corpus, expert labels | the wild, independent annotators | **low** (external truth) |
| 4 | Does the LLM-judge agree with humans? (**calibration**) | human-labeled set; inter-annotator agreement as ceiling | humans, blind to the tool | **low** if labelers ≠ author |
| 5 | Does enforcing it improve the product? (**value**) | A/B ablation with a *real* agent + independent grader | real runs | low |
| 6 | Do the cards predict real behavior? (**predictive validity**) | train/test split, out-of-sample | held-out sessions | **lowest** — the real prize |

Questions 1–2 are *software correctness*. Question 3 is *policy validity* — a
rule can be perfectly implemented and still be the wrong rule. Questions 4–5 are
*efficacy*. Question 6 is what OpenHarness is ultimately about: not "is this
checker accurate" but "does the module's **characterization** hold out of sample."

## Anti-cheat principles

1. **Provenance separation** — the entity that writes the checker does not write
   the labels. Blind labeling, or an independent oracle.
2. **Label from intent or an independent oracle** — never from the tool under
   test. Cross-implementation agreement (two tools built independently) is real
   evidence; self-agreement is not.
3. **Held-out / temporal split** — build on old data, evaluate on newer, unseen
   data, so the checker cannot be retrofit to the test.
4. **Spec-first and frozen** — author the golden set from the requirement, freeze
   it, *then* tune the checker.
5. **Mutation / metamorphic generation** — derive near-misses mechanically, so
   coverage is not limited to cases the author imagined.
6. **Inter-annotator agreement is the ceiling** — no judge can be "more accurate"
   than humans agree with one another; report that ceiling, not just the score.

## What our current benchmarks actually prove — and don't

Being explicit, because the whole point is not to overclaim.

### L1 — `benchmark/l1_conformance.py` — **synthetic**

- **Author:** one author, one session, wrote both checkers and labels. Labels
  were written from rule *intent*, not from checker output (which is why L1
  could, and did, catch two real `pii-guard` bugs — the checker disagreed with
  an intent-derived label).
- **Proves (Q1):** each checker *implements its specification* on a small,
  author-chosen set including adversarial near-misses. Implementation bugs
  surface here.
- **Does NOT prove:** (Q3) that the rules catch the real-world distribution of
  violations; (Q4) that the `prose-style` proxy judge agrees with humans; nothing
  a second, independent author couldn't have unconsciously biased. F1 = 1.00 on
  L1 means "no implementation bug on these 38 cases," **not** "this rule is
  correct or complete."
- **Provenance gap:** no author separation, no held-out split, no independent
  oracle. That is the honest weakness.

### L2 — `benchmark/l2_ablation.py` — **synthetic agent**

- **Proves (Q5, mechanism):** the *gating loop* works — reject-on-FAIL then
  retry drives residual violations to 0 with unchanged task completion, at a
  measured retry cost, on a controllable scripted agent.
- **Does NOT prove (Q5, efficacy):** that a *real* LLM agent produces better
  output under gating. The agent here is a stand-in whose violation rate we set;
  it demonstrates the intervention's mechanics, not its effect on a real model.

### L3 — `integrations/claude_code_hook.py` — **real interface, demo trace**

- **Proves:** the adapter maps real tool-call shapes to events and the pipeline
  runs live end-to-end (verified by `--selftest`).
- **Does NOT prove:** any accuracy or value claim — it is a plumbing/coverage
  demonstration.

### Not yet built

- **Q3 coverage** on real corpora, **Q4 judge calibration** against humans,
  **Q6 predictive validity** of the cards. These are the claims that would move
  the proposal from "plausible mechanism" to "demonstrated instrument."

## Real / sensible data sources, per module

With ethics caveats — **never commit real leaked secrets or private data.**

| Module | Independent oracle | Real(ish) corpus | Notes |
|--------|--------------------|------------------|-------|
| `no-secrets` | gitleaks / trufflehog rulesets | their labeled test suites; published example keys (AWS `AKIA…EXAMPLE`, GitGuardian benchmark) | strongest real option; use detector benchmarks, not the wild |
| `conventional-commits` | **commitlint** (a different implementation) | commit history of CC-mandating OSS (Angular, Vue) vs arbitrary repos | cross-tool agreement is genuinely non-circular |
| `pii-guard` | a schema-driven PII tagger you didn't write | real **schemas** from Spider / BIRD text-to-SQL, PII injected; label by schema | real query *logs* are private — synthesize over real schemas |
| `prose-style` | **human raters** (≥3, report agreement) | real README / docs corpus | the one module that genuinely needs humans; shipped scorer is a proxy |
| `tdd` | commit + CI timeline (reflog / Actions) | scarce; honest hard case | conformance is trivial to check; the interesting claim is *value* (Q5), not detection |

## The non-circular protocol we are proposing

1. **Freeze an intent-derived golden set** per module before tuning (spec-first).
2. **Add an independent oracle** wherever one exists (commitlint, gitleaks) and
   report *cross-tool agreement*, not self-accuracy.
3. **Held-out split**: evaluate on data the checker never saw; prefer a temporal
   split (older → newer).
4. **Human calibration** for the judge tier: blind labels from multiple raters,
   report agreement and the inter-rater ceiling.
5. **Real-agent ablation** (Q5): a live agent, gating vs off, graded by an
   independent rubric.
6. **Predictive validity** (Q6): cards from training sessions must predict
   held-out conformance. If they don't, we report that — the negative result is
   the honest finding, and finding it is the reason not to cheat.

## The standard we hold ourselves to

Every number in this repository is labeled **synthetic** or **real** and paired
with a "does not prove" clause. A harness that cannot survive that labeling is
not yet proven — and saying so is the difference between an evaluation and a
demo.
