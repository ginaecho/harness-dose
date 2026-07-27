"""Load the agent skills and link each to the harness module that holds its
lifted rule.

This is the machine-readable side of the ``skills/README.md`` story: every skill
declares, in its frontmatter, which behavioral rule was removed from its prose
and re-mounted as a module. The benchmark and demo use this link to show that
the rules under test came out of *real skills*, not out of thin air.

Deliberately dependency-free: a five-line frontmatter reader, no PyYAML.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Iterable

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    harness_module: str = ""
    lifted_rule: str = ""
    emits_events: tuple[str, ...] = ()
    path: str = ""


def _parse_frontmatter(text: str) -> dict[str, str | list[str]]:
    """Parse a minimal ``key: value`` / ``key: [a, b]`` YAML frontmatter block.

    Supports the handful of shapes the SKILL.md files use, including folded
    (``>-``) multi-line descriptions. Not a general YAML parser — intentionally.
    """
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end].strip("\n")
    data: dict[str, str | list[str]] = {}
    key: str | None = None
    folded: list[str] = []

    def flush() -> None:
        nonlocal folded, key
        if key is not None and folded:
            data[key] = " ".join(s.strip() for s in folded if s.strip())
        folded = []

    for line in block.splitlines():
        if line and not line[0].isspace() and ":" in line:
            flush()
            k, _, v = line.partition(":")
            key = k.strip()
            v = v.strip()
            if v in (">-", ">", "|", "|-"):
                folded = []
            elif v.startswith("[") and v.endswith("]"):
                data[key] = [x.strip() for x in v[1:-1].split(",") if x.strip()]
                key = None
            elif v:
                data[key] = v.strip().strip('"').strip("'")
                key = None
        elif key is not None and line.strip():
            folded.append(line)
    flush()
    return data


def load_skill(skill_md_path: str) -> Skill:
    with open(skill_md_path, encoding="utf-8") as f:
        fm = _parse_frontmatter(f.read())
    emits = fm.get("emits_events", [])
    return Skill(
        name=str(fm.get("name", "")),
        description=str(fm.get("description", "")),
        harness_module=str(fm.get("harness_module", "")),
        lifted_rule=str(fm.get("lifted_rule", "")),
        emits_events=tuple(emits) if isinstance(emits, list) else (),
        path=skill_md_path,
    )


def load_skills(skills_dir: str = SKILLS_DIR) -> list[Skill]:
    skills: list[Skill] = []
    if not os.path.isdir(skills_dir):
        return skills
    for name in sorted(os.listdir(skills_dir)):
        md = os.path.join(skills_dir, name, "SKILL.md")
        if os.path.isfile(md):
            skills.append(load_skill(md))
    return skills


def skill_for_module(module_id: str, skills: Iterable[Skill] | None = None) -> Skill | None:
    for s in (skills if skills is not None else load_skills()):
        if s.harness_module == module_id:
            return s
    return None
