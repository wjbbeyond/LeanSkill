#!/usr/bin/env python3
"""Validate a local LeanSkill installation."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path


def has_policy(path: Path, expected: bool) -> bool:
    if not path.exists():
        return False
    value = "true" if expected else "false"
    return re.search(
        rf"^\s*allow_implicit_invocation\s*:\s*{value}\s*$",
        path.read_text(encoding="utf-8", errors="replace"),
        re.MULTILINE | re.IGNORECASE,
    ) is not None


def user_skill_dirs(codex_skills: Path, shared_skills: Path) -> list[Path]:
    roots = [(codex_skills, True), (shared_skills, False)]
    result = []
    for root, exclude_system in roots:
        if not root.exists():
            continue
        for file in root.rglob("SKILL.md"):
            relative = file.relative_to(root)
            if exclude_system and relative.parts and relative.parts[0].startswith("."):
                continue
            if file.parent.name in {"leanskill-router", "project-dev-router"}:
                continue
            result.append(file.parent)
    return sorted(result)


def main() -> int:
    parser = argparse.ArgumentParser()
    default_codex = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    parser.add_argument("--codex-home", type=Path, default=default_codex)
    parser.add_argument("--shared-skills", type=Path, default=Path.home() / ".agents" / "skills")
    parser.add_argument("--global-agents", type=Path)
    parser.add_argument("--policy-manifest", type=Path)
    parser.add_argument("--require-explicit-user-skills", action="store_true")
    args = parser.parse_args()

    codex_home = args.codex_home.expanduser().resolve()
    config_path = codex_home / "leanskill" / "config.json"
    router = codex_home / "skills" / "leanskill-router"
    global_agents = (args.global_agents or codex_home / "AGENTS.md").expanduser().resolve()
    checks: dict[str, object] = {}

    checks["config_exists"] = config_path.is_file()
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.is_file() else {}
    lab_root = Path(config.get("lab_root", ""))
    catalog_path = Path(config.get("catalog_path", ""))
    checks["lab_root_exists"] = lab_root.is_dir()
    checks["catalog_exists"] = catalog_path.is_file()
    catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.is_file() else {"skills": [], "plugins": []}
    checks["catalog_schema"] = catalog.get("schema_version") == 1
    checks["catalog_skill_count"] = len(catalog.get("skills", []))
    checks["enabled_plugin_count"] = sum(1 for item in catalog.get("plugins", []) if item.get("status") == "installed-enabled")

    checks["router_skill_exists"] = (router / "SKILL.md").is_file()
    checks["router_implicit"] = has_policy(router / "agents" / "openai.yaml", True)
    agents_text = global_agents.read_text(encoding="utf-8", errors="replace") if global_agents.is_file() else ""
    checks["global_agents_routes"] = "$leanskill-router" in agents_text
    checks["install_manifest_exists"] = (codex_home / "leanskill" / "install-manifest.json").is_file()

    targets = user_skill_dirs(codex_home / "skills", args.shared_skills.expanduser().resolve())
    explicit = [path for path in targets if has_policy(path / "agents" / "openai.yaml", False)]
    checks["user_skill_targets"] = len(targets)
    checks["user_skills_explicit_only"] = len(explicit)
    if args.require_explicit_user_skills:
        checks["all_user_skills_explicit_only"] = len(targets) == len(explicit)

    if args.policy_manifest:
        checks["policy_manifest_exists"] = args.policy_manifest.is_file()
        manifest = json.loads(args.policy_manifest.read_text(encoding="utf-8")) if args.policy_manifest.is_file() else {"records": []}
        checks["policy_manifest_records"] = len(manifest.get("records", []))
        checks["policy_manifest_matches_targets"] = len(manifest.get("records", [])) == len(targets)

    boolean_failures = [key for key, value in checks.items() if isinstance(value, bool) and not value]
    result = {"valid": not boolean_failures, "failures": boolean_failures, "checks": checks}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if boolean_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
