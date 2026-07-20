# Architecture

LeanSkill separates one-time new-project planning from native execution and slow capability maintenance.

```text
New-project request
        |
        v
LeanSkill Router -----> local verified catalog
        |                       ^
        | writes advisory plan |
        v                       |
docs/LEANSKILL_PLAN.md          |
        |                       |
        v                       |
Native Codex execution    LeanSkill Lab
                          discovery -> evaluation -> outcomes
```

## Planning layer

`skills/leanskill-router/` is explicit-only. The installed global instruction calls it once when planning a genuinely new project. It classifies project type, initial phase, quality, and risk/cost, then selects from catalog entries whose status is `preferred`, `available-explicit`, or `available-implicit`.

The deterministic helper proposes a route, emits the receipt before broad scans or tests, and writes `docs/LEANSKILL_PLAN.md`. The first pass is capped at five read-only command batches. The shortlist is advisory and missing capabilities become gaps, never automatic installations.

Planning-time ranking combines route fit, trust, availability, matching anonymous outcomes, native/Token comparison, context cost, and maintenance evidence. Unknown measurements contribute no points and reduce confidence. Repeated matching failure plus worse Token use can defer the initial plan to native Codex.

## Execution layer

After the initial plan, native Codex owns implementation, testing, debugging, phase transitions, and direct invocation of installed specialist Skills. An installed explicit-only Skill can be invoked by its exact name when supported by the saved plan or current task evidence. LeanSkill does not re-run automatically. The saved plan is context, not a whitelist, preload instruction, or permanent execution graph.

## Maintenance layer

LeanSkill Lab builds a local inventory and maintains candidate, verified, rejected, and gap records. Discovery and deep validation are separate operations. A verified candidate is not installed or promoted automatically.

## Policy layer

LeanSkill Guard can make user-installed skills explicit-only. It excludes system skills and both current and legacy router names. Each mutation records original hashes and backups; restore refuses to overwrite conflicting later edits.

## Local state

- Repository: schemas, fixtures, scripts, and public documentation
- `catalog/registry.json`: generated machine-local inventory, ignored by Git
- `state/outcomes.jsonl`: optional schema-limited anonymous outcomes, ignored by Git
- `~/.codex/leanskill/config.json`: active catalog location and `plan-once` mode
- `~/.codex/leanskill/install-manifest.json`: install and rollback state
- `~/.codex/backups/leanskill-*`: retained recovery data
