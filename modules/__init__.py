"""Shipped harness modules — a small starter *materia medica*.

Each module here is a self-contained unit: a scope you can point at, a check you
can run, and a price you can read. Import :data:`ALL` to mount the set, or cherry
-pick individual modules. Third parties are expected to publish their own the
same way — a module is just a :class:`openharness.module.HarnessModule`.
"""

from __future__ import annotations

from .tdd import MODULE as tdd
from .pii_guard import MODULE as pii_guard
from .conventional_commits import MODULE as conventional_commits
from .no_secrets import MODULE as no_secrets
from .prose_style import MODULE as prose_style

ALL = [tdd, pii_guard, conventional_commits, no_secrets, prose_style]

__all__ = ["ALL", "tdd", "pii_guard", "conventional_commits", "no_secrets", "prose_style"]
