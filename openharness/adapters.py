"""Adapters that turn a real agent's tool calls into harness events.

The layer watches an event stream; a real agent (Claude Code, an SDK agent, a
CI bot) speaks in *tool calls*. This module is the thin translation between the
two, so OpenHarness can plug onto an agent without the agent changing at all.

The mapping is deliberately conservative — it emits an event only when a tool
call clearly corresponds to one — and it is pure/dependency-free so it can run
inside a hook.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .events import Event, EventType

_CODE_EXT = (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb",
             ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".kt", ".swift", ".php")
_SQL_RE = re.compile(r"\b(select|insert|update|delete)\b[\s\S]*\b(from|into|set)\b", re.IGNORECASE)
_GIT_COMMIT_RE = re.compile(r"git\s+commit\b[\s\S]*?-m\s+(['\"])(?P<msg>.*?)\1", re.IGNORECASE)
_TEST_CMD_RE = re.compile(r"\b(pytest|go\s+test|npm\s+test|jest|cargo\s+test|mvn\s+test)\b",
                          re.IGNORECASE)


def _is_code(path: str) -> bool:
    return path.lower().endswith(_CODE_EXT)


def events_from_tool(tool_name: str, tool_input: dict[str, Any],
                     tool_response: Any, *, task_id: str, task_type: str) -> list[Event]:
    """Translate one tool call into zero or more harness events."""
    tool = (tool_name or "").lower()
    ev: list[Event] = []

    def mk(t: str, **payload: Any) -> Event:
        return Event(type=t, task_id=task_id, task_type=task_type, payload=payload)

    if tool in ("write", "edit", "multiedit", "create", "notebookedit", "update"):
        path = tool_input.get("file_path") or tool_input.get("path") or tool_input.get("notebook_path", "")
        content = (tool_input.get("content")
                   or tool_input.get("new_string")
                   or tool_input.get("new_source", "")) or ""
        ev.append(mk(EventType.FILE_WRITTEN, path=path, content=content))
        if _is_code(path):
            ev.append(mk(EventType.CODE_MODIFIED, files=[path]))
        return ev

    if tool == "bash":
        cmd = tool_input.get("command", "") or ""
        m = _GIT_COMMIT_RE.search(cmd)
        if m:
            ev.append(mk(EventType.COMMIT_CREATED, message=m.group("msg")))
        if _SQL_RE.search(cmd):
            ev.append(mk(EventType.QUERY_EXECUTED, sql=cmd))
        if _TEST_CMD_RE.search(cmd):
            status = _exit_status(tool_response)
            ev.append(mk(EventType.TEST_RUN,
                         status="passing" if status == 0 else "failing"))
        return ev

    return ev


def _exit_status(tool_response: Any) -> int:
    if isinstance(tool_response, dict):
        for k in ("exit_code", "exitCode", "returncode", "code"):
            if k in tool_response:
                try:
                    return int(tool_response[k])
                except (TypeError, ValueError):
                    return 0
        text = json.dumps(tool_response).lower()
        if "error" in text or "failed" in text:
            return 1
    return 0


# -- event persistence, so a per-invocation hook can rebuild session history --

def event_to_json(ev: Event) -> str:
    return json.dumps({
        "type": ev.type, "task_id": ev.task_id, "task_type": ev.task_type,
        "payload": ev.payload, "agent_id": ev.agent_id, "ts": ev.ts,
    })


def event_from_json(line: str) -> Event:
    d = json.loads(line)
    return Event(type=d["type"], task_id=d["task_id"], task_type=d["task_type"],
                 payload=d.get("payload", {}), agent_id=d.get("agent_id", "agent"),
                 ts=d.get("ts", 0))
