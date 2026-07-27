"""Precedence & conflict experiment (L5).

Reproduces the "four mistakes that came from ordering, not ignorance" as a
controlled study: the same four governance rules, embedded in a skill vs
re-mounted as an ordered harness layer, across a family of skills A–D. Shows
which mechanism fixes which failure class:

* contradiction (branch name, commit trailer) → explicit **precedence**
* scope error (reply governance)              → declarative **scope**
* authorization ambiguity (destructive act)   → deterministic **gate**

and that a FORGE-style static conflict scan flags the contradictions — but not
the under-specified failures — before anything runs.

Run ``python -m precedence.experiment`` (or ``make l5``).
"""
