# LeanSkill

LeanSkill is a local-first, evidence-aware capability planner for Codex. Its **Plan Once, Execute Native** mode selects an initial set of at most one primary Skill and two specialists for a genuinely new project, saves the plan, and then hands all execution and later Skill choices to native Codex.

> Use less context. Activate the right capability.

## Why

Large global skill libraries can increase context cost, create overlapping instructions, and make development workflows slower. Re-running a meta-router during ordinary development can create the same problem. LeanSkill therefore uses four routing dimensions—project type, initial phase, quality target, and risk/cost—once at new-project planning time. It ranks relevant candidates with explicit fit, trust, availability, field-outcome, native-overlap, context-cost, and maintenance signals; unknown measurements reduce confidence instead of becoming invented evidence.

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

Anonymous local outcome recording is off by default. Opt in during installation or upgrade:

```bash
python3 scripts/install.py install --record-outcomes
```

Records are schema-limited, stored in ignored local state, and cannot contain project names, paths, prompts, source, secrets, or free-form notes.

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

## Use: Plan Once, Execute Native

The global installer rule explicitly calls LeanSkill once for a genuinely new project. The Skill itself is explicit-only, so it does not auto-trigger for ordinary questions or development work.

Do not use LeanSkill automatically for existing projects, major features, implementation continuation, phase changes, failed gates, research, diagnosis, provider/API selection, or routine edits. After the initial plan, native Codex directly decides which installed specialist Skills add value. It may invoke an installed explicit-only Skill by the exact name in the saved plan or verified catalog; that is direct Skill use, not another LeanSkill route.

Explicitly request a new-project plan or later re-plan when needed:

```text
Use $leanskill-router once to create the initial capability plan for this new project.
```

For routine small edits, LeanSkill stays out of the way.

Run the deterministic helper directly:

```bash
python3 skills/leanskill-router/scripts/route.py \
  --project /path/to/project \
  --task "Build and verify a premium React interface" \
  --format markdown \
  --write-plan
```

The helper emits a short receipt before deep inspection and saves `docs/LEANSKILL_PLAN.md`. The saved shortlist is advisory, not preloaded and not a whitelist. It exposes a decision score and confidence for catalog Skills, not a claim that a Skill is objectively better; native Codex receives no invented score. High confidence requires repeated matching outcomes and a measured native/Token comparison.

An existing plan is not overwritten automatically. Only after the user explicitly requests re-planning, run the helper again with `--force-plan`.

LeanSkill Lab can record an enabled anonymous evaluation checkpoint outside the normal development loop:

```bash
python3 skills/leanskill-router/scripts/record_outcome.py \
  --project-type web --phase test --quality production --risk low \
  --primary build-web-apps:frontend-testing-debugging \
  --specialist browser:control-in-app-browser \
  --status local-success --gate lint=pass --gate e2e=pass \
  --token-efficiency unknown
```

## Validate

Unmarked legacy Global project capability routing instructions now require manual
migration before installation. The installer leaves the original file unchanged;
preserve custom rules when replacing that legacy section. Discovered plugin and
personal skill names no longer imply official or reviewed provenance. Policy
changes save all backups and the recovery manifest before writing any targets;
retain that manifest if a failure also prevents automatic rollback.

```bash
python3 scripts/validate_catalog.py evals/catalog.fixture.json
python3 scripts/evaluate_router.py \
  --catalog evals/catalog.fixture.json \
  --router skills/leanskill-router/scripts/route.py
python3 -m unittest discover -s tests -v
python3 skills/leanskill-router/scripts/record_outcome.py \
  --input evals/outcome.fixture.json --dry-run
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

`v0.2.1-beta` fixes planning for genuinely new, empty repositories. `v0.2.0-beta` introduced Plan Once, Execute Native, explicit-only invocation, a persisted advisory project plan, evidence-aware ranking, bounded first-pass inspection, anonymous local outcomes, negation-safe intent parsing, and Skill/plugin developer-tool routing. Real-project Token comparisons are still being collected; unknown efficiency remains explicitly unknown.

## License

Apache-2.0. See [LICENSE](LICENSE).
