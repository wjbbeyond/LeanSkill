# Evidence-aware value model

Use the decision score to rank relevant candidates in the one-time new-project plan, not to claim that a Skill is objectively better or to control later execution.

| Signal | Maximum | Meaning |
|---|---:|---|
| Route fit | 40 | Position in the narrow route pattern |
| Trust | 20 | Official/system provenance or reviewed local source |
| Availability | 10 | Preferred or currently routable state |
| Matching outcomes | 15 | Anonymous results for the same project type and phase |
| Context/native efficiency | 10 | Measured token comparison plus curated overlap/cost |
| Maintenance | 5 | Curated current/stale evidence |

Unknown outcome, context, native-overlap, and maintenance measurements receive zero points and reduce confidence. They are not failures.

One matching outcome raises confidence only to medium. High confidence requires at least three matching outcomes and a measured native/token comparison. Repeated failure plus worse token use creates a negative-optimization warning and makes native Codex the default for that route.

Do not invent a numeric score for native Codex. After the initial plan, native Codex may directly choose a different installed Skill based on the real implementation context without re-running LeanSkill.

Do not attribute blocked external integration to a Skill failure when its authorized local gates passed. Record it as `local-success-external-blocked` with generic blocker categories. Do not infer Token efficiency without a comparable native baseline; record `unknown`.
