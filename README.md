# OpenHarness

### See the harness. Share the harness. Prove the harness works.

[![CI](https://github.com/ginaecho/open-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/ginaecho/open-harness/actions/workflows/ci.yml)
[![DOI](https://img.shields.io/badge/DOI-pending%20first%20release-blue)](docs/zenodo.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Plug it onto any agent and watch the harness live: rule invoked → applied → pass
or fail, event by event. Break the black box. Learn which harness wins at what.

---

## Watch the story

A short walkthrough of the idea — why the harness is a black box, and what
lifting it into a plugin layer unlocks. The player below is embedded inline on
the GitHub README:

https://github.com/ginaecho/open-harness/raw/refs/heads/gc/openharness-plugin-layer/docs/media/OpenHarness_Story.mp4

▶ If your viewer doesn't render the player, [download the video](docs/media/OpenHarness_Story.mp4).

---

## The problem: the harness is a black box

Everyone who works seriously with agents builds a *harness* — the behavioral
rules that make the agent actually good: how it writes, how it develops code,
how it touches sensitive data. That craft knowledge lives *inside* the agent's
skills and prompt files, mixed in with everything else. You can't point at it,
can't inspect it, can't test it, so you can't compare it. And *when* the rules
fire is left to the agent's discretion, based on a title. That is not a harness
at all.

## The move: re-mount the rules as a layer above the agent

OpenHarness makes one architectural move: **remove behavioral rules from the
agent's skills and re-mount them as a plugin layer above the agent** — the way
middleware sits above application code, managed separately, swapped
independently.

Each rule becomes a **harness module**: a small unit with a declared **scope**
(*binds when the agent modifies code*, *binds when a query touches PII*), a
**conformance check**, and a **price**. Binding is decided by the layer, not by
the agent — the reins are held from outside. The agent underneath is unchanged:
it keeps its task skills and does its work; the layer watches and verifies from
above.

## What modularity unlocks

- **Observable.** A module has boundaries, so its activity is loggable:
  *this event → this module bound (with evidence) → the trace complied, or it
  didn't.* The harness becomes a stream of visible verdicts.
- **Testable.** A module is a unit, so you evaluate it like one: run the same
  task with it on and off (`on_off_delta`), score it against labeled runs
  (`measure_accuracy`), and record what each check costs by tier.

## The payoff: the harness-cards dashboard

Accumulate observation and testing over real usage and every module earns a
**harness card**. Each card answers, in numbers instead of anecdotes:

- **What is it good at?** — a competence score per task type (tdd nails
  `bug_fix`, scores 0 on `prototype`, so you know when *not* to use it).
- **Is it being followed?** — a live conformance verdict, split by severity.
- **What does it cost to enforce?** — the check tier, its accuracy, tokens per
  check. Enforcement as a displayed price.
- **Is it earning its place?** — a momentum trend across your recent sessions.
- **What's happening upstream?** — new versions from the source repo, impact
  analysis, and conflicts with your other modules.

> The harness is the object of study, not the agent. Observability tools X-ray
> one run to diagnose it; we characterize `tdd` itself — where it wins, where
> it's useless — as a reusable instrument. Clinical diagnosis vs. pharmacology:
> we build a **materia medica of harnesses**.

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

## Layout

```
openharness/     the layer:  module · events · harness · checks · trace · card · dashboard · evaluate · cli
modules/         the starter materia medica (tdd, pii-guard, …)
examples/        demo_session.py — end-to-end run that writes dashboard.html
tests/           pytest suite (harness semantics + card metrics)
docs/            architecture.md · zenodo.md
```

## Citing & DOI

OpenHarness is set up for a citable [Zenodo](https://zenodo.org) DOI on every
release. The one-time owner consent step and the release flow are documented in
[`docs/zenodo.md`](docs/zenodo.md). Metadata lives in
[`CITATION.cff`](CITATION.cff) and [`.zenodo.json`](.zenodo.json); after the
first release, drop the minted concept DOI into the badge above and
`CITATION.cff`.

## License

[MIT](LICENSE) © Gina Chen
