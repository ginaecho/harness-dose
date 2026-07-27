# Architecture

OpenHarness is one architectural move applied consistently: **take the
behavioral rules out of the agent and mount them above it.** Everything else is
a consequence of that move.

```
        ┌──────────────────────────────────────────────┐
        │            HARNESS LAYER  (this repo)          │
        │                                                │
        │   module ── scope ─┐                           │
        │   module ── scope ─┼─►  BindingEngine          │
        │   module ── scope ─┘        │                  │
        │                             ▼                  │
        │                     ConformanceCheck (tiered)  │
        │                             │                  │
        │                             ▼                  │
        │                     Observation stream ──► Cards│
        └───────────────▲────────────────────────────────┘
                        │  events (code.modified, query.executed, …)
        ┌───────────────┴────────────────────────────────┐
        │   AGENT (unchanged) — the test rig              │
        │   keeps its task skills, does the work          │
        └─────────────────────────────────────────────────┘
```

The agent never imports anything from here. It just emits events. The layer
watches from above and holds the reins.

## The five nouns

| Noun | File | What it is |
|------|------|------------|
| **Event** | `openharness/events.py` | one observable thing the agent did |
| **HarnessModule** | `openharness/module.py` | a rule: `scope` + `check` + `price` |
| **Harness** | `openharness/harness.py` | the plugin layer that binds and checks |
| **Observation** | `openharness/trace.py` | one row of the verdict stream |
| **HarnessCard** | `openharness/card.py` | a module characterized across sessions |

## The three properties the move buys

### 1. Binding is external

`Harness.observe(event)` asks every module's **scope** whether it applies. The
scope is a predicate over the event — `on_event("code.modified")`,
`on_event_when("query.executed", touches_pii, ...)`. If it binds, the layer runs
the **check**; the agent's opinion never enters. Each binding records *why* it
bound (`Binding.evidence`), so the decision is auditable.

### 2. Checks are priced

Every check declares a **tier** (`openharness/module.py :: CheckTier`):

| Tier | Cost | Accuracy | Example module |
|------|------|----------|----------------|
| `DETERMINISTIC` | free | 1.0 | `tdd` (reads the trace) |
| `STATIC` | cheap | ~0.97 | `pii-guard`, `no-secrets`, `conventional-commits` |
| `LLM_JUDGE` | priced | stated (e.g. 0.85) | `prose-style` |

The card prints the tier and the token cost, so enforcement is a *displayed
price*, not a hope.

### 3. Everything is a unit, so everything is measurable

- **Observable** — `Harness.trace` is an ordered list of `Observation`s. Each is
  `event → module → verdict` with evidence, severity, and tokens. That is the
  entire audit log.
- **Testable** — `openharness/evaluate.py` runs a module against labeled
  fixtures (`measure_accuracy`) or toggles it on/off over one session
  (`on_off_delta`). The card's numbers come from these, not from anecdote.

## Checks look *backward*, not forward

A conformance check receives the current event plus the task's prior events
(`history`). This keeps the model streaming — no waiting for the future — while
still expressing "test before code": when `code.modified` arrives, `tdd` looks
back for a `test.written`/`test.run` that preceded it in the *same task*. Task
histories are isolated, so a test in task A never satisfies a change in task B.

## Extending it

A module is just a `HarnessModule` value. Publish your own by exporting one from
any importable module; see `modules/tdd.py` for the smallest complete example.
Nothing about the layer is specific to the five shipped rules — they are a
starter *materia medica*, not the framework.
