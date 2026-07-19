# LeanSkill repository instructions

- Keep the always-on router concise. One primary skill and at most two specialists.
- Never install, enable, download, or execute a discovered candidate automatically.
- Treat `catalog/registry.json` as generated machine-local state; never commit it.
- Keep quarantined third-party source, backups, automation IDs, account data, and absolute user paths out of Git.
- Preserve dry-run, backup, hash-check, and rollback behavior for global mutations.
- Use `apply_patch` for repository edits. Run the full validation commands in README before release.
- Do not publish, create releases, or mutate external systems without explicit user authority.
