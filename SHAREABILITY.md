# Shareability boundary

LeanSkill is distributed as one repository with two layers:

1. `skills/leanskill-router/` — the installable runtime skill.
2. The repository scripts, catalog schema, evaluation fixtures, and documentation — LeanSkill Lab and Guard.

## Included

- Router instructions, references, deterministic helper, and sample profile
- Catalog schema and empty templates
- Inventory, evaluation, installation, validation, and policy scripts
- Synthetic evaluation fixtures
- Generic automation prompts and operating documentation

## Excluded

- Generated `catalog/registry.json`
- Absolute user paths and local configuration
- Backup manifests and original user files
- Quarantined third-party source code
- Automation IDs, project IDs, account data, secrets, and private reports

Marketplace packaging is intentionally deferred until the Beta has enough real-project evidence. The GitHub repository is the supported distribution channel for `v0.1.0-beta`.
