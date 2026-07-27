---
name: write-docs
description: >-
  Write user-facing documentation — READMEs, guides, release notes. Use when
  prose needs to explain a feature clearly. Produces documentation text.
harness_module: prose-style
lifted_rule: "Documentation must read clearly and avoid hype."
emits_events: [doc.written]
---

# Writing documentation

Explain the thing plainly. The quality bar — clear, concrete, hype-free — is
**not** enforced by your own judgment here; it is judged by the `prose-style`
module, which binds to every `doc.written` event and scores it. This is the one
module on an **LLM-judge tier**: its verdict is priced and only ~85% accurate,
and its card says so out loud.

## Steps

1. **Lead with what it does**, concretely, in the first sentence.
2. **Cut hype.** Avoid "blazing", "revolutionary", "game-changing", "seamless",
   "10x", and their friends. Short sentences.
3. **Show, don't sell.** Prefer an example to an adjective. Emit `doc.written`
   (content).

## What the agent emits

- `doc.written` (content) — the documentation text

`prose-style` (LLM-judge tier, minor severity) scores clarity and flags hype,
returning a verdict with its rationale. Because the check is priced and fallible,
its cost and stated accuracy are shown on its harness card — enforcement as a
displayed price, not a hope.
