# LeanSkill

LeanSkill is a local-first capability router for Codex. It keeps the always-on layer small, selects at most one primary skill and two specialists, and separates runtime routing from slower skill discovery and validation.

> Use less context. Activate the right capability.

## Why

Large global skill libraries can increase context cost, create overlapping instructions, and make development workflows slower. LeanSkill uses four routing dimensions—project type, phase, quality target, and risk/cost—to select a bounded capability set from a local verified catalog.

LeanSkill does **not** automatically install newly discovered skills, deploy projects, publish content, spend money, or mutate external systems.

## Components

- **LeanSkill Router** — the global Codex skill in `skills/leanskill-router/`.
- **LeanSkill Catalog** — a generated local inventory plus lifecycle metadata.
- **LeanSkill Lab** — discovery, quarantine, evaluation, and maintenance scripts.
- **LeanSkill Guard** — explicit-only policy tooling with backup and rollback.

## Requirements

- macOS or Linux
- Python 3.10+
- Codex CLI or Desktop with skill support
- `gh` only if you plan to contribute or publish a fork

LeanSkill has no runtime Python dependencies.

## Install

Clone the repository, inspect the dry run, then install:

```bash
git clone https://github.com/wjbbeyond/LeanSkill.git
cd LeanSkill
python3 scripts/install.py install --dry-run
python3 scripts/install.py install
```

The installer:

- copies `leanskill-router` into `$CODEX_HOME/skills` (or `~/.codex/skills`)
- adds a marked, removable LeanSkill block to global `AGENTS.md`
- creates `~/.codex/leanskill/config.json`
- builds a machine-local `catalog/registry.json`
- records backups and hashes for conflict-safe uninstall

Start a new Codex conversation after installation so the skill list is refreshed.

Check or remove the installation:

```bash
python3 scripts/install.py status
python3 scripts/install.py uninstall --dry-run
python3 scripts/install.py uninstall
```

## Optional context hardening

The default installer does not rewrite other skills. To make user-installed skills explicit-only, inspect the plan and opt in:

```bash
python3 scripts/policy_manager.py --dry-run
python3 scripts/policy_manager.py --apply
```

The command writes a rollback manifest. Restore with:

```bash
python3 scripts/policy_manager.py --restore <manifest-path>
```

Official plugin caches are not modified.

## Use

LeanSkill routes automatically for new projects, major features, phase changes, and material quality or risk changes. Force a route when needed:

```text
Use $leanskill-router to select the smallest verified skill set for this task.
```

For routine small edits, LeanSkill stays out of the way.

Run the deterministic helper directly:

```bash
python3 skills/leanskill-router/scripts/route.py \
  --project /path/to/project \
  --task "Build and verify a premium React interface" \
  --format markdown
```

## Validate

```bash
python3 scripts/validate_catalog.py evals/catalog.fixture.json
python3 scripts/evaluate_router.py \
  --catalog evals/catalog.fixture.json \
  --router skills/leanskill-router/scripts/route.py
python3 -m unittest discover -s tests -v
python3 scripts/release_check.py
```

## Safety model

- Discovery is read-only and cannot install candidates.
- Deep validation handles at most three candidates per run.
- Community popularity is a discovery signal, not trust evidence.
- Installation, global policy changes, deployment, publishing, and external writes require explicit authority.
- Generated local catalogs, backups, automation IDs, and quarantined sources are excluded from Git.

See [Operating Model](docs/OPERATING_MODEL.md), [Architecture](docs/ARCHITECTURE.md), and [Threat Model](docs/THREAT_MODEL.md).

## Status

`v0.1.0-beta` is an early public release. The routing constraints and synthetic evaluation suite are stable; real-project token and routing-quality measurements are still being collected.

## License

Apache-2.0. See [LICENSE](LICENSE).
