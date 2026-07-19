---
name: leanskill-router
description: Route software, web, mobile, game, backend, AI, and design work to the smallest verified set of Codex skills and plugins. Use at a new project or major feature start, at phase transitions, when quality or risk changes, or when the user asks which skills, plugins, or workflow to use.
---

# LeanSkill Router

Choose capabilities before execution without turning the project into a heavyweight meta-workflow.

## Routing contract

1. Inspect the actual project, its local instructions, and the user's requested outcome.
2. Classify four dimensions:
   - project type
   - current phase
   - quality target
   - risk and cost
3. Read `references/routing-matrix.md`. Read `references/quality-gates.md` when UI, release, security, migration, paid APIs, or external writes are involved.
4. Consult the verified catalog configured in `~/.codex/leanskill/config.json`. If it is missing, run `scripts/route.py` without a catalog and state that the route is provisional.
5. Select at most one primary skill and two specialist skills. Prefer an already enabled official skill, then a verified local skill. Do not invoke two skills that own the same decision.
6. Emit a short route receipt before substantial implementation:
   - detected profile
   - selected primary and specialists with one-line reasons
   - gates and checkpoints
   - capability gaps
7. Invoke only the selected skills. Re-route only at a major phase boundary, a failed gate, or a material change in scope, quality, risk, or platform.

## Hard rules

- A small, routine code edit does not need a new route unless risk or UI quality changes.
- Never install, enable, download, or execute a newly discovered skill or plugin automatically.
- Never let discovery block useful work when Codex native capability is sufficient.
- Treat design authority and implementation authority as separate roles. For premium UI, require a visual target, design tokens, responsive states, and browser/simulator evidence.
- Do not deploy, publish, spend money, use production data, or mutate external systems without the user's authority.
- Prefer evidence from the real checkout and runtime over generic workflow ceremony.
- Log an unmet capability to LeanSkill Lab instead of expanding the current run.

## Local helper

Use the deterministic helper for a reproducible first pass:

```bash
python3 scripts/route.py --project <project-path> --task "<requested outcome>" --format markdown
```

The helper proposes a route; the agent remains responsible for checking project instructions and user intent.
