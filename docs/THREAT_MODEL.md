# Threat model

## Protected assets

- Codex global instructions and skill configuration
- User-installed skills and their metadata
- Secrets, production data, accounts, and external systems
- Local projects and generated evidence

## Main threats

1. A malicious candidate skill attempts code execution, secret access, persistence, or broad filesystem writes.
2. A popular but redundant skill increases context cost or introduces conflicting authority.
3. An installer overwrites user configuration without a recoverable copy.
4. An uninstall operation destroys later user edits.
5. Generated local inventory leaks usernames, paths, account identifiers, or private project names into Git.
6. A router treats a recommendation as permission to install, deploy, publish, or spend money.

## Controls

- Discovery never downloads or executes candidate code.
- Deep validation is capped at three candidates and uses quarantine for static inspection.
- Promotion requires provenance, license, pinned version, compatibility, security, outcome, and cost evidence.
- Global changes require explicit commands, dry-run support, backups, hashes, and conflict-safe rollback.
- The installer uses a delimited AGENTS block and does not replace unrelated instructions.
- Machine-local catalogs, backups, quarantine contents, and automation state are ignored by Git.
- The router sets `auto_install` to false and adds authority/rollback gates for high-risk work.

## Non-goals

LeanSkill is not a sandbox, malware scanner, package manager, deployment system, or guarantee that a third-party skill is safe. Users remain responsible for reviewing external code and platform permissions.
