# Routing matrix

Use this as a decision map, not as a command to activate everything in a row.

## Four dimensions

| Dimension | Values | Effect |
|---|---|---|
| Project type | web, iOS, cross-platform, macOS, game, backend/API, AI agent, data/viz, content/docs | Chooses the primary technical authority |
| Phase | discovery, design, architecture, implementation, test, performance, security, release, maintenance | Chooses the current owner; earlier-phase skills stop when their artifact is accepted |
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
| Data visualization | matching data-viz implementation skill | browser test, accessibility/performance |
| Security-sensitive change | implementation owner stays primary | one security audit specialist |
| Release/CI failure | release or CI fixer | platform deploy specialist only when authorized |

If the preferred capability is not enabled and verified, use native Codex capability and record a gap. A plugin recommendation is not permission to install it.

## Phase boundaries

- Discovery ends with a testable problem statement and constraints.
- Design ends with accepted references, tokens, states, and interaction intent.
- Architecture ends with interfaces, data ownership, risk decisions, and a bounded plan.
- Implementation ends when the requested slice works locally.
- Verification ends with proportional tests plus real UI/runtime evidence where applicable.
- Release ends only after the user-authorized environment is verified.
