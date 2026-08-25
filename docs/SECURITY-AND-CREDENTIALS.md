# Security and Credential Standard

- Persistent credentials belong in an OS/user-controlled store, not a project repository.
- Projects store only a profile reference or non-secret selector.
- Agents use shared credential resolvers and adapters; they do not scan arbitrary files.
- Health reports may include boolean presence, source class, HTTP status, and error class only.
- GET fallback after 401 is allowed only for public reads. Writes fail closed.
- Environment overrides must be explicit, process-only, and disabled by default.
- `.gitignore` is defense in depth, not permission to put secrets in ignored files.
- Credential rotation, revocation, expiry, and owner must be trackable without revealing the value.
