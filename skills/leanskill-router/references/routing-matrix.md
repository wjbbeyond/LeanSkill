# Routing matrix

Use this once as a new-project planning map, not as a command to activate everything in a row. After the plan is saved, native Codex owns all later capability decisions.

## Four dimensions

| Dimension | Values | Effect |
|---|---|---|
| Project type | web, iOS, cross-platform, macOS, game, backend/API, AI agent, developer tooling/Skill, data/viz, content/docs | Chooses the primary technical authority |
| Initial phase | discovery, design, architecture, implementation, test, performance, security, release, maintenance | Helps choose the initial advisory capability owner only |
| Quality | functional, production, premium-visual | Raises evidence and design gates; does not add skills by itself |
| Risk/cost | low, medium, high | Adds security, migration, budget, rollback, or human-approval gates |

## Preferred route patterns

| Situation | Primary | Optional specialists |
|---|---|---|
| Web discovery/design | `frontend-design` | `design-taste-frontend`, product-design audit when enabled |
| React/web implementation | `build-web-apps:frontend-app-builder` | `build-web-apps:react-best-practices`, `build-web-apps:shadcn` |
| Web verification | `build-web-apps:frontend-testing-debugging` | Browser or Chrome control; web performance |
| SwiftUI implementation | `build-ios-apps:swiftui-ui-patterns` | view refactor, performance audit |
| iOS verification | `build-ios-apps:ios-simulator-browser` | debugger, memory/performance tools |
| 2D/3D game | game-studio skill matching the engine | game UI, sprite/asset pipeline, playtest |
| Backend/API | `backend-architect` | `api-design-principles`, database or migration specialist |
| AI agent | provider's official agent SDK skill | backend architecture, strict schema/evaluation specialist |
| Codex Skill or plugin maintenance | `skill-creator` or `plugin-creator` | testing/review only when it owns a distinct gate |
| Data visualization | matching data-viz implementation skill | browser test, accessibility/performance |
| Security-sensitive change | implementation owner stays primary | one security audit specialist |
| Release/CI failure | release or CI fixer | platform deploy specialist only when authorized |

If the preferred capability is not enabled and verified, use native Codex capability and record a gap. A plugin recommendation is not permission to install it.

## Project execution boundaries

- Save the initial result to `docs/LEANSKILL_PLAN.md`.
- Do not preload every planned Skill; invoke a specialist only when its expertise is relevant.
- Treat the saved shortlist as advisory rather than a permanent whitelist.
- Let native Codex handle discovery, design, architecture, implementation, verification, release, and maintenance transitions.
- Do not re-run LeanSkill at those transitions or after failed gates unless the user explicitly requests re-planning.
- Count a selected Skill's required Skill dependencies toward the three-capability planning limit.
