# Governance command conventions

Every non-underscore Markdown file in this directory is a user-invocable slash command. Each command must include YAML frontmatter with a `description`, plus the sections **Preflight**, **Plan**, **Commands**, **Verification**, **Summary**, and **Next Steps**.

Commands must preserve the repository's public/private boundary: use `reports/local/` for runtime records, never print registry paths or project identifiers unnecessarily, and treat `goal`/`full_access` as explicitly bounded write authority with mandatory warning, risk, recommendation, and human-follow-up reporting. They do not authorize scope expansion or unrecorded writes.
