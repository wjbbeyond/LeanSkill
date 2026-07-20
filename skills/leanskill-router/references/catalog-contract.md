# Catalog contract

The router reads the path in `~/.codex/leanskill/config.json` and supports the legacy `~/.codex/skill-lab/config.json` location during migration:

```json
{
  "schema_version": 1,
  "lab_root": "/path/to/LeanSkill",
  "catalog_path": "/path/to/LeanSkill/catalog/registry.json"
}
```

Only catalog entries with `preferred`, `available-explicit`, or `available-implicit` status are routable. `candidate`, `quarantined`, `rejected`, `cached-not-enabled`, and `missing` entries are never selected.

Every entry needs a stable id, invocation name, source path, origin, status, implicit-invocation policy, capabilities, and trust tier. Machine-specific paths belong only in the local registry and must not be included in a shared package.

Entries may add a `value_profile` with `context_cost`, `native_overlap`, and `maintenance`. Omit or mark unknown values that have not been measured. Field outcomes live separately in the ignored local JSONL file configured by `feedback_path`; they never add project names, paths, source, prompts, secrets, or free-form notes to the catalog.
