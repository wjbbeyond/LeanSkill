# Architecture

LeanSkill separates fast routing from slow capability maintenance.

```text
User task
   |
   v
LeanSkill Router -----> local verified catalog
   |                         ^
   | selects 1 + up to 2     |
   v                         |
Codex execution        LeanSkill Lab
                       discovery -> quarantine -> verification
```

## Runtime layer

`skills/leanskill-router/` is the only LeanSkill component intended for implicit invocation. It classifies project type, phase, quality, and risk/cost, then selects from catalog entries whose status is `preferred`, `available-explicit`, or `available-implicit`.

The deterministic helper proposes a route; Codex still checks repository instructions and user intent. Missing capabilities become gaps, never automatic installations.

## Maintenance layer

LeanSkill Lab builds a local inventory and maintains candidate, verified, rejected, and gap records. Discovery and deep validation are separate operations. A verified candidate is not installed or promoted automatically.

## Policy layer

LeanSkill Guard can make user-installed skills explicit-only. It excludes system skills and both current and legacy router names. Each mutation records original hashes and backups; restore refuses to overwrite conflicting later edits.

## Local state

- Repository: schemas, fixtures, scripts, and public documentation
- `catalog/registry.json`: generated machine-local inventory, ignored by Git
- `~/.codex/leanskill/config.json`: active catalog location
- `~/.codex/leanskill/install-manifest.json`: install and rollback state
- `~/.codex/backups/leanskill-*`: retained recovery data
