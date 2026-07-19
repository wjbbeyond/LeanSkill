# Operating model

## Lifecycle

1. `discovered`: link and basic metadata only.
2. `candidate`: relevant to a recorded capability gap and eligible for review.
3. `quarantined`: source pinned locally for code and behavior inspection.
4. `verified`: passed security, compatibility, usefulness, and token-cost evaluation.
5. `available-explicit`: installed but invoked only through an explicit route.
6. `preferred`: best current option for a narrow route.
7. `rejected`: failed or redundant; record the reason and recheck condition.

No state transition implies installation. Installation is a separate user-authorized action.

## Source order

1. Already installed and verified local capability
2. Official Codex plugin directory
3. OpenAI-maintained skill repository
4. First-party vendor repository
5. Portable official skill from another agent ecosystem
6. Community source with pinned provenance

## Candidate score

| Dimension | Weight |
|---|---:|
| Capability gap coverage | 30 |
| Measured outcome improvement | 25 |
| Trust and security | 25 |
| Maintenance and compatibility | 10 |
| Token, time, and workflow cost | 10 |

Promotion requires at least 75/100, no critical security failure, repeatable evaluation evidence, and no simpler native or installed alternative with comparable results. Visual skills also require blind review of rendered output, not prompt quality alone.

## Discovery report fields

- source, owner, repository, license, release or commit
- matched capability gap and project types
- current popularity/maintenance evidence with date
- overlapping installed/native capabilities
- security and supply-chain observations
- expected benefit and evaluation plan
- lifecycle recommendation

## Monthly cleanup

Downgrade or reject entries that are unused, redundant, unmaintained, incompatible, security-sensitive without benefit, or consistently slower/more expensive than native Codex. Never remove user data or uninstall globally from an automated review.
