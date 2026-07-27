"""The event stream the agent-under-test emits as it works.

The agent is the *test rig*. It does its task and, as it goes, emits events —
it modified code, it ran a query, it wrote a commit. The harness layer never
tells the agent what to do; it only watches this stream and decides which
modules bind. Events are the layer's entire window onto the agent.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any

_seq = itertools.count(1)


@dataclass(frozen=True)
class Event:
    """One observable thing the agent did.

    ``ts`` is a logical sequence number, not wall-clock, so traces are
    deterministic and replayable (and so scripts that forbid ``Date.now`` still
    reproduce byte-for-byte).
    """

    type: str
    task_id: str
    task_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    agent_id: str = "agent"
    ts: int = field(default_factory=lambda: next(_seq))

    def get(self, key: str, default: Any = None) -> Any:
        return self.payload.get(key, default)


# Canonical event types the built-in modules key off. Modules may invent their
# own; these are just the vocabulary the shipped examples share.
class EventType:
    CODE_MODIFIED = "code.modified"
    TEST_WRITTEN = "test.written"
    TEST_RUN = "test.run"
    FILE_WRITTEN = "file.written"
    QUERY_EXECUTED = "query.executed"
    COMMIT_CREATED = "commit.created"
    DOC_WRITTEN = "doc.written"


def event(type: str, task_id: str, task_type: str, **payload: Any) -> Event:
    """Ergonomic constructor: ``event(EventType.COMMIT_CREATED, "t1", "bug_fix", message=...)``."""
    return Event(type=type, task_id=task_id, task_type=task_type, payload=payload)
