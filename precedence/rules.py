"""The four governance rules, lifted out of skills into harness modules — plus
the two harness-default rules they contradict.

Each rule is a :class:`GovModule`: a declared **source**, a declared **scope**
(which action types it binds to — no agent discretion), and the **directives**
it issues. Two of the four collide head-on with a harness default (branch name,
commit trailer); those collisions are what a static conflict scan catches. The
other two (reply scope, destructive authorization) issue directives that nothing
contradicts — they are under-specification, not contradiction, and so are
invisible to the static scan by design.
"""

from __future__ import annotations

from dataclasses import dataclass

from openharness.govern import Directive, Polarity, Source

# action types the skills emit
BRANCH_CREATE = "branch.create"
COMMIT_CREATE = "commit.create"
REPLY_WRITE = "reply.write"
FILE_DELETE = "file.delete"
FORCE_PUSH = "force.push"


@dataclass(frozen=True)
class GovModule:
    id: str
    source: Source
    scope: frozenset[str]
    directives: tuple[Directive, ...]
    kind: str            # "authoritative" (project/conversation) | "harness_default"
    failure_class: str   # C1..C4 the rule is about
    lifted_from: str     # the skill prose this rule was extracted from


# --- the four authoritative rules (from AGENT.md / the conversation) ---------

branch_policy = GovModule(
    id="branch-policy",
    source=Source.PROJECT,
    scope=frozenset({BRANCH_CREATE}),
    directives=(
        Directive("branch-policy", Source.PROJECT, "branch.name", Polarity.FORBID,
                  "claude", "branch names must not contain 'claude'"),
        Directive("branch-policy", Source.PROJECT, "branch.name", Polarity.REQUIRE,
                  "^gc/", "branch names must use the gc/ prefix"),
    ),
    kind="authoritative", failure_class="C1", lifted_from="branch-naming clause of AGENT.md",
)

no_assistant_trailer = GovModule(
    id="no-assistant-trailer",
    source=Source.PROJECT,
    scope=frozenset({COMMIT_CREATE}),
    directives=(
        Directive("no-assistant-trailer", Source.PROJECT, "commit.trailer", Polarity.FORBID,
                  "coauthor", "no Co-Authored-By / session trailer on commits"),
    ),
    kind="authoritative", failure_class="C2", lifted_from="commit-trailer clause of AGENT.md",
)

reply_scope = GovModule(
    id="reply-scope",
    source=Source.PROJECT,
    scope=frozenset({REPLY_WRITE}),
    directives=(
        Directive("reply-scope", Source.PROJECT, "reply.style", Polarity.REQUIRE,
                  "project", "AGENT.md §5 governs chat replies, not just documents"),
    ),
    kind="authoritative", failure_class="C3", lifted_from="§5 of AGENT.md (reply governance)",
)

confirm_destructive = GovModule(
    id="confirm-destructive",
    source=Source.PROJECT,
    scope=frozenset({FILE_DELETE, FORCE_PUSH}),
    directives=(
        Directive("confirm-destructive", Source.PROJECT, "authorization", Polarity.REQUIRE,
                  "explicit", "destructive actions require explicit prior authorization"),
    ),
    kind="authoritative", failure_class="C4", lifted_from="confirm-before-destructive clause",
)

# --- the two harness/system defaults that contradict the project rules -------

harness_branch_default = GovModule(
    id="harness-branch-default",
    source=Source.HARNESS,
    scope=frozenset({BRANCH_CREATE}),
    directives=(
        Directive("harness-branch-default", Source.HARNESS, "branch.name", Polarity.REQUIRE,
                  "claude", "session config mandated a claude/... branch"),
    ),
    kind="harness_default", failure_class="C1", lifted_from="session harness config",
)

harness_commit_trailer = GovModule(
    id="harness-commit-trailer",
    source=Source.HARNESS,
    scope=frozenset({COMMIT_CREATE}),
    directives=(
        Directive("harness-commit-trailer", Source.HARNESS, "commit.trailer", Polarity.REQUIRE,
                  "coauthor", "session config mandated a Co-Authored-By trailer"),
    ),
    kind="harness_default", failure_class="C2", lifted_from="session harness config",
)


ALL_MODULES = [branch_policy, no_assistant_trailer, reply_scope, confirm_destructive,
               harness_branch_default, harness_commit_trailer]


def all_directives():
    return [d for m in ALL_MODULES for d in m.directives]
