"""no-secrets — no credential ever gets written to a file.

Binds whenever a file is written; conforms if the content carries no hardcoded
secret. Static tier: a set of credential patterns. Critical severity — a leaked
key is the canonical thing a harness exists to stop.
"""

from __future__ import annotations

from openharness.checks import forbid, on_event
from openharness.events import Event, EventType
from openharness.module import (CheckTier, HarnessModule, Price, Severity, Upstream)

_SECRETS = {
    "aws access key": r"AKIA[0-9A-Z]{16}",
    "generic api key": r"(api[_-]?key|secret)['\"]?\s*[:=]\s*['\"][A-Za-z0-9]{16,}['\"]",
    "private key block": r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "slack token": r"xox[baprs]-[0-9A-Za-z-]{10,}",
    "bearer token": r"bearer\s+[A-Za-z0-9._-]{24,}",
}


def _check(event: Event, history: list[Event]):
    content = event.get("content", "") or ""
    return forbid(content, _SECRETS,
                  ok_msg="no hardcoded secrets", severity=Severity.CRITICAL)


MODULE = HarnessModule(
    id="no-secrets",
    name="No Hardcoded Secrets",
    summary="Files written must contain no API keys, tokens, or private keys.",
    scope=on_event(EventType.FILE_WRITTEN),
    check=_check,
    price=Price.for_tier(CheckTier.STATIC),
    upstream=Upstream(repo="openharness/modules-no-secrets", version="3.1.0"),
    tags=("security", "secrets"),
)
