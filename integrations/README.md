# Live integration — plug OpenHarness onto a real agent

This is **L3**: the harness watching an actual coding session, not a simulation.
It proves the "plug it onto any agent" claim by wiring OpenHarness to Claude Code
through a `PostToolUse` hook. The agent is unchanged; the layer observes from
above.

## How it works

```
Claude Code tool call ──stdin JSON──▶ claude_code_hook.py
      (Edit/Write/Bash/…)                    │
                                             ▼
                        adapters.events_from_tool()  →  harness events
                                             │
                                    Harness(ALL).observe()
                                             │
                        ┌────────────────────┴───────────────────┐
                        ▼                                         ▼
             verdicts → your terminal (stderr)      .openharness/events.jsonl
                                                                  │
                                                     --dashboard  ▼
                                                          session_dashboard.html
```

`openharness/adapters.py` maps tool calls to events conservatively:

| Tool call | Event(s) emitted |
|-----------|------------------|
| `Write` / `Edit` / `MultiEdit` / `NotebookEdit` | `file.written`; plus `code.modified` for source files |
| `Bash: git commit -m "…"` | `commit.created` |
| `Bash` containing a SQL statement | `query.executed` |
| `Bash: pytest` / `go test` / `npm test` … | `test.run` (status from exit code) |

## Wire it up

1. Copy the `hooks` block from [`settings.example.json`](settings.example.json)
   into your project's `.claude/settings.json`.
2. Work normally in Claude Code. Verdicts stream to your terminal as you go:
   ```
   [openharness] [ 3] query.executed → pii-guard ✗ fail (critical) — unmasked PII in query: email
   ```
3. Build the dashboard from the accumulated session anytime:
   ```bash
   python3 integrations/claude_code_hook.py --dashboard -o session_dashboard.html
   ```

The hook **never blocks** the agent — a malformed payload or an unmapped tool is
a no-op (exit 0). It only observes and records. (Gating — rejecting a step on a
critical FAIL — is demonstrated in `benchmark/l2_ablation.py`; turning the hook
into a blocking `PreToolUse` gate is a small extension left deliberately opt-in.)

## Verify without Claude Code

```bash
python3 integrations/claude_code_hook.py --selftest
```

Feeds representative tool calls (a hardcoded key, a raw-email query, a bad commit,
a failing test then an edit) through the exact pipeline and asserts the right
modules fire.

## Other agents

`events_from_tool()` takes plain `(tool_name, tool_input, tool_response)` dicts,
so the same adapter works for an Agent SDK loop, a CI bot, or any harness that
can name its tool calls — not just Claude Code.
