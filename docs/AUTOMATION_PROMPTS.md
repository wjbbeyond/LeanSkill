# Optional automation prompts

These prompts are templates. Installing LeanSkill does not create recurring tasks.

## Weekly discovery

Run weekly with a cost-efficient model. Read the operating model, catalog templates, gaps, candidates, rejections, and recent reports. Search official Codex/OpenAI sources first, then first-party vendor repositories, then reputable community discussions. Record sources and dates. Add at most ten deduplicated candidates. Do not download, clone, install, import, execute, enable, or source candidates. Do not modify global Codex state or other projects. Write a short no-change report when nothing material changed.

## Biweekly deep validation

Run every two weeks with a stronger reasoning model. Select at most three candidates tied to real gaps. Verify provenance, license, pinned release or commit, maintenance, compatibility, scripts, dependencies, network/write scope, secret handling, supply-chain risk, overlap, measured benefit, and token/time cost. Static source copies may be placed only in quarantine. Do not execute candidate code or install dependencies. Passing candidates enter `catalog/verified.json`; they are not installed or preferred automatically.

## Monthly cleanup

Review preferred and available entries for usage, redundancy, maintenance, compatibility, security, token cost, and outcome quality. Recommend downgrade or removal, but do not mutate global state automatically.
