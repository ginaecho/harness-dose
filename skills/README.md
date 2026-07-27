# Skills — the agent's task knowledge (with the behavioral rules *lifted out*)

These are real, loadable agent skills (Claude Code `SKILL.md` format). They are
the **test rig** for OpenHarness: an agent following one of these skills emits
the event stream the harness layer watches.

The whole point of OpenHarness is one move — **take the behavioral rule out of
the skill and re-mount it as a harness module above the agent.** So each skill
here has had its behavioral rule *removed from the prose* and replaced with a
single machine-readable line in the frontmatter:

```yaml
harness_module: tdd        # the lifted rule now lives in modules/tdd.py
lifted_rule: "Write the failing test before the code that passes it."
```

The skill still says *what* to do; the harness module says *how it must be done*
and — unlike a sentence buried in prose — it can be pointed at, logged, tested,
and priced.

| Skill | Task | Lifted rule → module |
|-------|------|----------------------|
| [`bug-fix`](bug-fix/SKILL.md) | fix a reported bug | test-first → [`tdd`](../modules/tdd.py) |
| [`data-query`](data-query/SKILL.md) | answer a data question in SQL | mask PII → [`pii-guard`](../modules/pii_guard.py) |
| [`commit-changes`](commit-changes/SKILL.md) | commit work | message format → [`conventional-commits`](../modules/conventional_commits.py) |
| [`write-file`](write-file/SKILL.md) | write a source/config file | no secrets → [`no-secrets`](../modules/no_secrets.py) |
| [`write-docs`](write-docs/SKILL.md) | write documentation | clear, hype-free → [`prose-style`](../modules/prose_style.py) |

## Before → after (the lift, shown on `bug-fix`)

**Before** — the rule is buried in the skill, discretionary, invisible, untestable:

> ### Fixing a bug
> 1. Reproduce it. **You should usually write a failing test first, then make it
>    pass — but use your judgment; for small fixes a test may be overkill.**
> 2. Change the code. 3. Verify.

Who decides when "usually" and "your judgment" apply? The agent does, from a
title. That is not a harness.

**After** — the rule is gone from the prose and re-mounted as a module the layer
binds deterministically (`modules/tdd.py`), so *every* code change on a bug-fix
task is checked, with evidence, at zero token cost. The skill ([`bug-fix/SKILL.md`](bug-fix/SKILL.md))
now only carries the task, plus the one-line pointer to the module that holds it.

That is the entire OpenHarness idea, made concrete in five skills.
