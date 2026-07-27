---
name: write-file
description: >-
  Create or overwrite a source or configuration file. Use when adding modules,
  configs, scripts, or fixtures. Produces file contents on disk.
harness_module: no-secrets
lifted_rule: "Files written must contain no API keys, tokens, or private keys."
emits_events: [file.written, code.modified]
---

# Writing a file

Write the file's contents. The rule that no credential is ever committed is
**not** a reminder in this prose; it is enforced by the `no-secrets` module,
which binds to every `file.written` event and fails, at critical severity, on any
hardcoded secret.

## Steps

1. **Compose** the file contents.
2. **Secrets → config.** Read credentials from environment variables or a secret
   manager; never inline an API key, token, or private key. Emit `file.written`
   (path, content).
3. If it is source code, also emit `code.modified`.

## What the agent emits

- `file.written` (path, content) — the file
- `code.modified` (files) — when the file is code

`no-secrets` (static tier, critical severity) scans the content against a set of
credential patterns (AWS keys, bearer/slack tokens, private-key blocks, assigned
API keys) and verdicts it.
