import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openharness.adapters import (event_from_json, event_to_json,
                                  events_from_tool)
from openharness.events import EventType
from openharness.skills import load_skills, skill_for_module


def test_write_tool_maps_to_file_and_code_events():
    evs = events_from_tool("Write", {"file_path": "a.py", "content": "x=1"}, {},
                           task_id="t", task_type="s")
    types = {e.type for e in evs}
    assert EventType.FILE_WRITTEN in types and EventType.CODE_MODIFIED in types


def test_non_code_file_only_file_written():
    evs = events_from_tool("Write", {"file_path": "notes.md", "content": "hi"}, {},
                           task_id="t", task_type="s")
    assert [e.type for e in evs] == [EventType.FILE_WRITTEN]


def test_bash_git_commit_maps_to_commit_event():
    evs = events_from_tool("Bash", {"command": "git commit -m \"fix(x): y\""}, {},
                           task_id="t", task_type="s")
    assert evs and evs[0].type == EventType.COMMIT_CREATED
    assert evs[0].get("message") == "fix(x): y"


def test_bash_sql_maps_to_query_event():
    evs = events_from_tool("Bash", {"command": "psql -c 'SELECT email FROM users'"}, {},
                           task_id="t", task_type="s")
    assert any(e.type == EventType.QUERY_EXECUTED for e in evs)


def test_bash_test_run_status_from_exit_code():
    passing = events_from_tool("Bash", {"command": "pytest -q"}, {"exit_code": 0},
                               task_id="t", task_type="s")
    failing = events_from_tool("Bash", {"command": "pytest -q"}, {"exit_code": 1},
                               task_id="t", task_type="s")
    assert passing[0].get("status") == "passing"
    assert failing[0].get("status") == "failing"


def test_unmapped_tool_is_noop():
    assert events_from_tool("Read", {"file_path": "a.py"}, {}, task_id="t", task_type="s") == []


def test_event_json_roundtrip_preserves_ts():
    evs = events_from_tool("Write", {"file_path": "a.py", "content": "x"}, {},
                           task_id="t", task_type="s")
    back = event_from_json(event_to_json(evs[0]))
    assert back.type == evs[0].type and back.ts == evs[0].ts and back.payload == evs[0].payload


def test_skills_link_to_modules():
    skills = load_skills()
    assert len(skills) == 5
    for s in skills:
        assert s.harness_module and s.lifted_rule
    assert skill_for_module("tdd").name == "bug-fix"
    assert skill_for_module("pii-guard").name == "data-query"
