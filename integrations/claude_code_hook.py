#!/usr/bin/env python3
"""OpenHarness ⟷ Claude Code — a PostToolUse hook.

Wire this as a `PostToolUse` hook and OpenHarness watches a *real* coding session
from above: each tool call becomes an event, the mounted modules bind and
verdict it, and the stream accumulates into `.openharness/events.jsonl`. Build
the dashboard from that log at any time.

This is the "plug it onto any agent" claim, made literal — the agent is
unchanged; the harness observes.

Usage
-----
As a hook, Claude Code pipes the tool-call JSON to stdin::

    "hooks": {
      "PostToolUse": [
        { "matcher": "Edit|Write|MultiEdit|Bash|NotebookEdit",
          "hooks": [ { "type": "command",
                       "command": "python3 integrations/claude_code_hook.py" } ] }
      ]
    }

Build the dashboard from the accumulated session::

    python3 integrations/claude_code_hook.py --dashboard -o session.html

Self-test without Claude Code (feeds sample tool calls through the pipeline)::

    python3 integrations/claude_code_hook.py --selftest
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openharness.adapters import event_from_json, event_to_json, events_from_tool
from openharness.harness import Harness
from modules import ALL

LOG_DIR = os.environ.get("OPENHARNESS_DIR", ".openharness")
EVENTS_LOG = os.path.join(LOG_DIR, "events.jsonl")
TASK_TYPE = os.environ.get("OPENHARNESS_TASK_TYPE", "session")


def _load_events(path: str):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [event_from_json(line) for line in f if line.strip()]


def _append_events(path: str, events) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as f:
        for ev in events:
            f.write(event_to_json(ev) + "\n")


def handle_hook(payload: dict) -> int:
    """Process one PostToolUse payload; log events and print any verdicts."""
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    tool_response = payload.get("tool_response", {})
    session_id = payload.get("session_id", "session")

    prior = _load_events(EVENTS_LOG)
    new_events = events_from_tool(tool_name, tool_input, tool_response,
                                  task_id=session_id, task_type=TASK_TYPE)
    if not new_events:
        return 0

    # replay history so backward-looking checks (e.g. tdd) see prior events,
    # then observe only the new ones and surface their verdicts.
    h = Harness(ALL, session_id=session_id)
    for ev in prior:
        h.observe(ev)
    before = len(h.trace)
    for ev in new_events:
        h.observe(ev)
    produced = h.trace.observations[before:]

    _append_events(EVENTS_LOG, new_events)

    for o in produced:
        # hook stderr is surfaced to the user by Claude Code
        print(f"[openharness] {o.render_line()}", file=sys.stderr)
    return 0


def build_dashboard(out: str) -> int:
    from openharness.card import build_cards
    from openharness.dashboard import render_dashboard
    events = _load_events(EVENTS_LOG)
    h = Harness(ALL, session_id="live")
    h.run(events)
    cards = build_cards(ALL, h.trace)
    with open(out, "w") as f:
        f.write(render_dashboard(cards.values()))
    print(f"wrote {out} from {len(events)} events / {len(h.trace)} observations")
    return 0


def selftest() -> int:
    """Feed representative tool calls through the pipeline; assert verdicts appear."""
    global EVENTS_LOG
    import tempfile
    tmp = tempfile.mkdtemp()
    EVENTS_LOG = os.path.join(tmp, "events.jsonl")
    fake_aws = "AKIA" + "IOSFODNN7" + "EXAMPLE"  # fragmented: not a scannable literal
    samples = [
        {"session_id": "s", "tool_name": "Write",
         "tool_input": {"file_path": "config.py", "content": f'KEY = "{fake_aws}"'}},
        {"session_id": "s", "tool_name": "Bash",
         "tool_input": {"command": "psql -c \"SELECT email FROM users\""}},
        {"session_id": "s", "tool_name": "Bash",
         "tool_input": {"command": "git commit -m 'did stuff'"}},
        {"session_id": "s", "tool_name": "Bash",
         "tool_input": {"command": "pytest -q"}, "tool_response": {"exit_code": 1}},
        {"session_id": "s", "tool_name": "Edit",
         "tool_input": {"file_path": "bug.py", "new_string": "return a + b"}},
    ]
    for p in samples:
        handle_hook(p)
    events = _load_events(EVENTS_LOG)
    h = Harness(ALL, session_id="s")
    h.run(events)
    from openharness.module import Verdict
    fails = [o for o in h.trace if o.verdict == Verdict.FAIL]
    print(f"\nselftest: {len(events)} events, {len(h.trace)} observations, "
          f"{len(fails)} violations caught")
    assert any(o.module_id == "no-secrets" and o.verdict == Verdict.FAIL for o in h.trace), \
        "expected no-secrets to fire on the hardcoded key"
    assert any(o.module_id == "pii-guard" and o.verdict == Verdict.FAIL for o in h.trace), \
        "expected pii-guard to fire on raw email"
    assert any(o.module_id == "tdd" and o.verdict == Verdict.PASS for o in h.trace), \
        "expected tdd to pass (failing test ran before the edit)"
    print("selftest OK ✓")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="OpenHarness Claude Code hook")
    ap.add_argument("--dashboard", action="store_true", help="build dashboard from the session log")
    ap.add_argument("--selftest", action="store_true", help="run the pipeline self-test")
    ap.add_argument("-o", "--out", default="session_dashboard.html")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if args.dashboard:
        return build_dashboard(args.out)

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # nothing to do; never block the agent
    return handle_hook(payload)


if __name__ == "__main__":
    raise SystemExit(main())
