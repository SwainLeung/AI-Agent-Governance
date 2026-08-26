# Configuration Agent Contract

## Scope

This directory contains public machine-readable contracts, schemas, templates, and Dashboard information architecture.

## Operating rules

- Treat JSON schemas and execution contracts as public interfaces and preserve backward compatibility unless a migration is documented.
- Keep local paths, project identifiers, credentials, provider values, and runtime state out of public files.
- Update the consuming documentation and generators when a contract field or meaning changes.
- Prefer explicit enums, required fields, and fail-closed defaults over permissive inference.
- Keep `project-roots.json` generic; private registrations belong only in the ignored local registry.
- Keep `project-operation-policy.json` as the public source for execution scopes and startup/switch gates; project-specific scope assignments belong only in the private registry.

## Verification

Run `python scripts/validate_governance.py` after contract changes. If behavior changes, also run the relevant generator and inspect the generated private/local output without committing it.

`README.md` explains the repository role of this directory. This file governs Agent changes inside it.
