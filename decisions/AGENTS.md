# Decisions Agent Contract

## Scope

This directory contains sanitized public decision examples only.

## Operating rules

- Never commit real project names, local paths, credentials, private prompts, production logs, or copied deployment details.
- Examples must preserve the decision shape: reviewer, scope, timestamp, artifact hash, evidence, expiry, and rollback reference where applicable.
- Do not represent an example as a live approval or as evidence that a project operation occurred.
- Real decisions belong in ignored private runtime records and must remain outside public Git.

## Verification

Run `python scripts/validate_governance.py` and scan changed files for local identifiers and secrets before handoff.

`README.md` explains the repository role of this directory. This file governs Agent changes inside it.
