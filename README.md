# HarnessDose

### See your harness. Tune your harness. Know it works.

[![CI](https://github.com/ginaecho/open-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/ginaecho/open-harness/actions/workflows/ci.yml)
[![DOI](https://zenodo.org/badge/1314056228.svg)](https://zenodo.org/badge/latestdoi/1314056228)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Plug it onto any agent and watch your harness live: rule invoked → applied → pass
or fail, event by event. Break the black box. Learn which harness wins at what.

> The Python package and repository are named `openharness` / `open-harness`;
> **HarnessDose** is the project name — the *materia medica* framing where every
> rule is characterized like a dose you can measure.

---

## Watch the story

A short walkthrough of the idea — why the harness is a black box, and what
lifting it into a plugin layer unlocks.

[![HarnessDose — the story (click for the full narrated video)](docs/media/OpenHarness_Story.gif)](docs/media/OpenHarness_Story.mp4)

▶ The preview above plays inline. **[Click it for the full narrated video](docs/media/OpenHarness_Story.mp4)** (with audio).

---

## The problem: your harness is a black box

Everyone who works seriously with agents builds a *harness* — the behavioral
rules that make the agent actually good: how it should write, how it should
develop code, how it should touch sensitive data. Your harness is deeply personal
and project-specific: you tune it yourself, for your setup, through months of
trial and error, chasing the workflow that finally clicks.

But you're tuning blind. This craft knowledge lives *inside* the agent's skills
and prompt files, mixed in with everything else — you can't easily point at any
one rule, so testing whether it helps means designing a bespoke evaluation,
running the task with and without it, and reading the traces by hand, every
single time. It's doable, but it costs hours you don't have, so in practice almost
no one does it. And when and how these rules get used? Mostly, you let the agent
decide, based on a title. Then that is not a harness at all — it's a wish.

## The move: re-mount the rules as a layer above the agent

Our core idea is one architectural move: **move behavioral rules out of the
agent's skills, and re-mount them as a plugin layer above the agent** — the way
middleware sits above application code, managed separately, tuned independently.

Each rule becomes a **harness module**: a small unit with a declared **scope**
(*binds when the agent modifies code*, *binds when a query touches PII*), a
**conformance check**, and a **price**. Binding is decided by the layer, not by
the agent's discretion — the reins are finally held from outside. The agent
underneath stays unchanged: it keeps its task skills and does its work; the
harness layer watches and verifies from above.

## From buried text to a measurable object

The point isn't modularity for its own sake — plenty of things are already
modular. The point is that a rule with a boundary becomes something you can
*instrument*: a variable you can log, score, and chart, instead of a few lines of
instructions buried in a prompt whose effect you can only guess at. That's the
shift from craft to measurement, and it's what makes a dashboard possible.

- **Observable.** Once a module has boundaries, its every activation is an event
  you can capture: *this happened → this module bound (with the evidence that
  triggered it) → the trace complied, or it didn't.* The harness stops being an
  invisible influence buried in context and becomes a stream of verdicts you watch
  in real time — the difference between suspecting a rule fired and seeing it fire,
  pass, or fail on screen.
- **Testable.** A module is a unit with a scope and check defined once, so the
  evaluation becomes *standing* instead of bespoke: after you declare it, every
  future session scores the module automatically — no hand-rolled test design per
  rule. Run the same task with the module on and off and measure the difference;
  count its passes and failures per task type; record what each check costs
  (deterministic trace check ≈ free, static rule ≈ cheap, LLM judge ≈ priced, with
  stated accuracy). The hours of manual evaluation collapse into a number that
  accrues on its own.

## The payoff: your harness cards dashboard

Accumulate that observation and testing over your real usage, and every module
earns a **harness card** — and the cards form your dashboard, the transparency you
need to tune well. Each card answers, with numbers instead of hunches:

- **What is it good at?** — a competence profile per task type: `tdd` scores 92 on
  bug fixing but 38 on prototyping, so you know when to switch it on and when to
  leave it off.
- **Is it being followed?** — a live conformance verdict: passes, failures, and
  errors caught, split by severity (critical vs. minor).
- **What does it cost you?** — the check tier, its accuracy, and tokens per check —
  so you can weigh whether a rule is worth its price in your loop.
- **Is it earning its place?** — a momentum trend: which of your modules are
  pulling their weight in real sessions, and which are dead weight you can retire.
- **What's happening upstream?** — news from each module's parent: new versions
  from its source repo, impact analysis ("this upstream change would fail 2 of your
  recent runs"), conflicts with your other modules, and modules worth trying.

Together, the dashboard turns "which harness gives me the best workflow?" from a
months-long feel into a question you can read off the cards.

## What makes this different: the harness is the object of study, not the agent

Observability tools study the agent — the trace is an X-ray, the goal is
diagnosis. We invert it: the **harness module is the object, the agent is just the
test rig.** You don't want to understand agent #1187; you want to characterize
`tdd` (test-driven development — write the failing test first, then the code that
passes it) — where it wins, where it's useless — as an instrument in your kit.
It's clinical diagnosis vs. pharmacology: they examine one patient's run; we build
you a *materia medica of harnesses* that tells you which instrument to reach for
given the task in front of you.

## Why this matters

Skills define *what* agents do. Security policy decides *whether* they may.
**HarnessDose takes the *how* out of the black box — and puts it on a dashboard
you can tune by.**

---

## Quick start

```bash
pip install -e .          # no runtime dependencies; Python ≥ 3.9
python -m examples.demo_session
```

That replays three sessions through five mounted modules, prints the verdict
stream, runs the A/B evaluations, and writes a self-contained
**`dashboard.html`** you can open or publish anywhere.

Use it directly:

```python
from openharness import Harness
from openharness.events import event, EventType
from openharness.card import build_cards
from openharness.dashboard import render_dashboard
from modules import ALL

h = Harness(ALL)
h.observe(event(EventType.CODE_MODIFIED, task_id="t1", task_type="bug_fix"))
for o in h.trace:
    print(o.render_line())
#   [  1] code.modified    → tdd  ✗ fail (minor)  — code changed with no failing test written first

cards = build_cards(ALL, h.trace)
open("dashboard.html", "w").write(render_dashboard(cards.values()))
```

## What ships

Five starter modules spanning every tier and severity — a small *materia
medica*, not the framework:

| Module | Binds when | Check tier | Severity |
|--------|------------|-----------|----------|
| `tdd` | code is modified | deterministic (free) | minor |
| `pii-guard` | a query touches a PII column | static | **critical** |
| `no-secrets` | a file is written | static | **critical** |
| `conventional-commits` | a commit is created | static | minor |
| `prose-style` | a document is written | LLM judge (priced, ~85%) | minor |

A module is just a `HarnessModule` value — export your own from any importable
module. See [`docs/architecture.md`](docs/architecture.md) for the design and
[`modules/tdd.py`](modules/tdd.py) for the smallest complete example.

Each module is the behavioral rule **lifted out of a real skill** in
[`skills/`](skills) — `skills/bug-fix` → `tdd`, `skills/data-query` → `pii-guard`,
and so on. The skill says *what* to do; the module holds the *how* the layer
enforces. That before/after lift is the whole idea, shown concretely.

## Proving it works

"It works" is three separable claims — each proved differently. All reproducible
with `make prove` / `make test`; full write-up in
[`docs/proving-it-works.md`](docs/proving-it-works.md). A step-by-step,
case-by-case verification guide is in
[`docs/how-it-was-tested.md`](docs/how-it-was-tested.md). The hard part is
*evaluating a harness without grading its own homework* —
[`docs/evaluation-methodology.md`](docs/evaluation-methodology.md) decomposes
that into six questions, states what each benchmark does and does **not** prove,
and marks every dataset synthetic vs real.

- **L1 — it *measures* correctly.** Every module scored as a violation classifier
  over a 38-trace labeled corpus with adversarial near-misses → **F1 = 1.00**
  after the benchmark caught and we fixed two real `pii-guard` bugs (a leaked
  `ssn`, a false-flagged table name), now pinned as regression tests.
- **L2 — enforcing it *improves outcomes*.** A/B ablation, 8 tasks × 30 seeds,
  same seeded decisions both arms: residual violations **50% → 0%** with **task
  success unchanged**, at ~4 retries/session. It even *measures* the
  `tdd`-on-prototype friction the cards claim.
- **L3 — it *plugs onto a real agent*.** A Claude Code `PostToolUse` hook turns
  live tool calls into events and streams verdicts; `--selftest` verifies the
  pipeline end-to-end. See [`integrations/`](integrations).
- **L5 — it fixes *ordering* failures, the ones that actually bite.** Rules
  interact: two in scope at once, resolved in the wrong order, and the agent errs
  *while following a rule*. [`precedence/`](precedence) reproduces a real
  four-mistake incident across a skill family and shows **externalizing isn't the
  fix — the ordering is** (embedded 0/4 clean, externalized+bad-order 0/4,
  externalized+right-order **4/4**), with a FORGE-style static conflict scan that
  catches the contradictions *before* running. A **live-agent** run (16 isolated,
  memoryless opus subagents) crosses to efficacy: **25% → 0%** violations, and
  pinpoints that the *only* failure surviving a capable model is
  under-specification (destructive action on ambiguous authorization), not
  contradiction — validating the incident's own conclusion. See
  [`docs/precedence.md`](docs/precedence.md).

## Built on Microsoft's Agent Governance Toolkit

HarnessDose composes with Microsoft's
[Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit)
(AGT, MIT): **AGT enforces, HarnessDose characterizes and proves.** The four
lifted precedence rules compile into an AGT `PolicyDocument` and are enforced by
AGT's real `PolicyEvaluator` (`priority` = our precedence) — verified in-container,
every decision matching native L5. AGT is an optional dependency
(`pip install agent-governance-toolkit-core`; `make agt`); the code degrades
gracefully when it's absent. Full mapping and pitch in
[`docs/agt-integration.md`](docs/agt-integration.md).

## Layout

```
openharness/     the layer:  module · events · harness · checks · trace · card · dashboard · evaluate · adapters · skills · govern · agt · cli
modules/         the starter materia medica (tdd, pii-guard, …)
skills/          real agent skills; each module is a rule lifted from one
benchmark/       L1 conformance + L2 ablation + reports/
precedence/      L5 — precedence/conflict layer, the A–D skill family, live-agent + AGT demos + reports/
integrations/    L3 — Claude Code hook + tool→event adapters
examples/        demo_session.py — end-to-end run that writes dashboard.html
tests/           pytest suite (47 tests: semantics, cards, benchmark, integration, precedence, AGT)
docs/            architecture · proving-it-works · how-it-was-tested · precedence · evaluation-methodology · agt-integration · zenodo
```

## Citing & DOI

HarnessDose is set up for a citable [Zenodo](https://zenodo.org) DOI on every
release. The one-time owner consent step and the release flow are documented in
[`docs/zenodo.md`](docs/zenodo.md). Metadata lives in
[`CITATION.cff`](CITATION.cff) and [`.zenodo.json`](.zenodo.json); after the
first release, drop the minted concept DOI into the badge above and
`CITATION.cff`.

## License

[MIT](LICENSE) © Gina Chen
