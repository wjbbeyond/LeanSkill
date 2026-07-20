# Quality and safety gates

## Premium visual gate

Before UI implementation, require:

- a named visual direction or reference set
- typography, color, spacing, radius, elevation, and motion tokens
- loading, empty, error, disabled, success, and destructive states
- mobile and desktop layout intent, or native size-class intent
- accessibility and reduced-motion expectations

Before completion, capture the real rendered surface at representative sizes. Compare hierarchy, rhythm, density, contrast, states, and interaction feel. Source-code review alone is not visual verification.

## Production gate

Require relevant automated tests, failure paths, observability, configuration separation, and a rollback path. Fake or dry-run evidence must be labeled and cannot replace real-provider or real-runtime evidence when the user requested it.

## High-risk gate

Authentication, payments, secrets, production data, database migrations, destructive operations, public publishing, paid APIs, and deployment require explicit scope, bounded impact, rollback, and user authority. Add at most one specialist for the dominant risk.

## Stop conditions

Stop expanding the workflow when the selected route can satisfy the acceptance criteria. Log optional improvements for later. A failed gate is handled by native Codex and does not trigger LeanSkill; re-plan only when the user explicitly requests it.
