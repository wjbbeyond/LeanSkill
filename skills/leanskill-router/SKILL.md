---
name: leanskill-router
description: Create a one-time, evidence-aware capability plan for a genuinely new software, web, mobile, game, backend, AI, or design project. Use only when global/project instructions explicitly require it for new-project planning, or when the user explicitly asks for $leanskill-router, a skill/plugin plan, or capability re-routing. Do not use automatically for existing-project work, feature implementation, phase changes, failures, research, status, diagnosis, provider selection, or routine edits.
---

# LeanSkill Router

Create the initial capability plan, then hand execution to native Codex. Formal mode: **Plan Once, Execute Native**.

## Routing contract

1. Confirm this is either a genuinely new-project planning task or an explicit user-requested re-route. If `docs/LEANSKILL_PLAN.md` already exists and the user did not explicitly request re-planning, stop using this Skill and let native Codex continue.
2. Run a bounded first pass over the actual project, its local instructions, and the user's requested outcome. Before the route receipt, use at most five read-only command batches: local instructions, root manifests, Git/status, at most one authoritative planning document, and the deterministic helper. Do not run tests, broadly scan implementation files, or read multiple reports yet.
3. Classify four dimensions:
   - project type
   - current phase
   - quality target
   - risk and cost
4. Read `references/routing-matrix.md`. Read `references/quality-gates.md` when UI, release, security, migration, paid APIs, or external writes are involved.
5. Consult the verified catalog configured in `~/.codex/leanskill/config.json`. If it is missing, run `scripts/route.py` without a catalog and state that the route is provisional.
6. Select at most one primary skill and two specialist skills. Compare route fit, trust, availability, matching anonymous outcomes, native overlap, context cost, and maintenance evidence. Unknown measurements lower confidence; never invent them. Read `references/value-model.md` when comparing candidates or interpreting feedback. Do not invoke two skills that own the same decision. Count any Skill that a selected Skill requires as a selected capability; never hide transitive activation beyond the three-capability limit.
7. Run the deterministic helper and emit its route receipt verbatim before substantial implementation. Never invent, adjust, or append numeric scores. The receipt includes:
   - detected profile
   - selected primary and specialists with decision score, confidence, and one-line reasons
   - gates and checkpoints
   - capability gaps
8. Persist the plan to `docs/LEANSKILL_PLAN.md` with `--write-plan`. Treat the shortlist as advisory, not as a permanent whitelist or a command to preload every Skill.
9. End LeanSkill routing. Native Codex owns implementation, testing, debugging, and later capability choices. Do not automatically re-route at phase boundaries, failed gates, scope changes, or quality/risk changes. Re-run LeanSkill only when the user explicitly requests it.

## Hard rules

- Do not invoke LeanSkill merely because work is complex, high risk, UI-facing, entering a new phase, or failing a gate.
- Do not invoke LeanSkill for an existing project, a major feature in an existing project, implementation continuation, Q&A, status, diagnosis, research, API/provider selection, or a routine edit unless the user explicitly requests re-routing.
- Never install, enable, download, or execute a newly discovered skill or plugin automatically.
- Never let discovery block useful work when Codex native capability is sufficient.
- Prefer native Codex when repeated matching evidence shows a skill both fails more often and consumes more tokens. A heuristic score without field outcomes is not proof of value.
- Do not assign a numeric score to native Codex unless the deterministic helper provides one.
- After the one-time plan, let native Codex directly invoke any installed Skill that adds concrete value. It may use the exact invocation name for an installed explicit-only Skill; this is direct Skill use, not LeanSkill re-routing. The initial shortlist does not prohibit later specialist use.
- Treat design authority and implementation authority as separate roles. For premium UI, require a visual target, design tokens, responsive states, and browser/simulator evidence.
- Do not deploy, publish, spend money, use production data, or mutate external systems without the user's authority.
- Prefer evidence from the real checkout and runtime over generic workflow ceremony.
- Log an unmet capability to LeanSkill Lab instead of expanding the current run.

## Local helper

Use the deterministic helper for a reproducible first pass:

```bash
python3 scripts/route.py --project <project-path> --task "<requested outcome>" --format markdown --write-plan
```

The helper proposes a one-time advisory plan; native Codex remains responsible for project instructions, user intent, execution, and later Skill choices. Use `--force-plan` only for an explicit user-requested re-route.

Outcome recording belongs to explicit LeanSkill Lab evaluation, not the normal project execution loop. When enabled, use `scripts/record_outcome.py` only with schema-limited aggregate data; use `unknown` when no native baseline exists.
