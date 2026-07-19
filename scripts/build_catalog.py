#!/usr/bin/env python3
"""Build a local Codex skill and plugin catalog from actual filesystem state."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PREFERRED = {
    "leanskill-router",
    "frontend-design",
    "build-web-apps:frontend-app-builder",
    "build-web-apps:frontend-testing-debugging",
    "build-web-apps:react-best-practices",
    "build-ios-apps:swiftui-ui-patterns",
    "build-ios-apps:ios-simulator-browser",
    "browser:control-in-app-browser",
    "chrome:control-chrome",
}

REVIEWED_LOCAL = {
    "design-taste-frontend", "design-taste-frontend-v1", "gpt-taste", "minimalist-ui",
    "industrial-brutalist-ui", "high-end-visual-design", "redesign-existing-projects",
    "full-output-enforcement", "image-to-code", "imagegen-frontend-web",
    "imagegen-frontend-mobile", "brandkit", "gsap-core", "gsap-frameworks",
    "gsap-performance", "gsap-plugins", "gsap-react", "gsap-scrolltrigger",
    "gsap-timeline", "gsap-utils",
}

CAPABILITY_RULES = {
    "frontend": r"front.?end|react|vue|svelte|ui|ux|web app|shadcn",
    "visual-design": r"design|taste|visual|brand|typography|color|image.to.code",
    "ios": r"ios|swift|swiftui|xcode|simulator",
    "game": r"game|phaser|three|sprite|webgl",
    "backend": r"backend|api|database|postgres|server|cloudflare|worker",
    "testing": r"test|debug|qa|audit|review",
    "security": r"security|iam|secret|compliance",
    "animation": r"gsap|motion|animation|scrolltrigger",
    "documentation": r"document|docs|pdf|presentation|spreadsheet",
    "automation": r"automation|workflow|agent",
}


def parse_frontmatter(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    name = path.parent.name
    description = ""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            for line in parts[1].splitlines():
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip().strip("\"'") or name
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip().strip("\"'")
    return name, description


def implicit_policy(skill_dir: Path) -> bool:
    path = skill_dir / "agents" / "openai.yaml"
    if not path.exists():
        return True
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^\s*allow_implicit_invocation\s*:\s*(true|false)\s*$", text, re.MULTILINE | re.IGNORECASE)
    return match is None or match.group(1).lower() == "true"


def capabilities(name: str, description: str) -> list[str]:
    value = f"{name} {description}".lower()
    result = [label for label, pattern in CAPABILITY_RULES.items() if re.search(pattern, value)]
    return result or ["general"]


def stable_id(origin: str, invocation: str, path: Path) -> str:
    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:10]
    return f"{origin}:{invocation}:{digest}"


def make_entry(skill_file: Path, origin: str, prefix: str | None = None) -> dict[str, Any]:
    name, description = parse_frontmatter(skill_file)
    invocation = f"{prefix}:{name}" if prefix else name
    implicit = implicit_policy(skill_file.parent)
    status = "preferred" if invocation in PREFERRED else "available-implicit" if implicit else "available-explicit"
    if origin == "official-plugin":
        trust = "official-plugin"
    elif name == "leanskill-router":
        trust = "local-system"
    elif name in REVIEWED_LOCAL:
        trust = "reviewed-local"
    else:
        trust = "local-unverified" if origin == "personal" else "community-local"
    return {
        "id": stable_id(origin, invocation, skill_file.parent),
        "name": name,
        "invocation": invocation,
        "description": description,
        "path": str(skill_file.parent.resolve()),
        "origin": origin,
        "status": status,
        "implicit_invocation": implicit,
        "capabilities": capabilities(invocation, description),
        "trust_tier": trust,
    }


def skill_files(root: Path, exclude_system: bool = False) -> Iterable[Path]:
    if not root.exists():
        return []
    files = []
    for path in root.rglob("SKILL.md"):
        relative = path.relative_to(root)
        if exclude_system and relative.parts and relative.parts[0].startswith("."):
            continue
        files.append(path)
    return sorted(files)


def plugin_inventory() -> tuple[list[dict[str, str]], list[tuple[str, Path]]]:
    try:
        process = subprocess.run(["codex", "plugin", "list"], check=False, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return [], []
    plugins: list[dict[str, str]] = []
    enabled: list[tuple[str, Path]] = []
    marketplace = "unknown"
    for line in process.stdout.splitlines():
        market = re.match(r"Marketplace `([^`]+)`", line)
        if market:
            marketplace = market.group(1)
            continue
        columns = re.split(r"\s{2,}", line.strip())
        if len(columns) < 3 or "@" not in columns[0] or columns[0] == "PLUGIN":
            continue
        full_name, status = columns[0], columns[1]
        name = full_name.split("@", 1)[0]
        item = {"name": name, "marketplace": marketplace, "status": "unknown", "version": "", "path": ""}
        if status == "installed, enabled" and len(columns) >= 4:
            item.update(status="installed-enabled", version=columns[2], path=columns[3])
            enabled.append((name, Path(columns[3])))
        elif status == "not installed":
            item.update(status="not-installed", path=columns[-1])
        plugins.append(item)
    return plugins, enabled


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--codex-skills", type=Path, default=Path.home() / ".codex" / "skills")
    parser.add_argument("--shared-skills", type=Path, default=Path.home() / ".agents" / "skills")
    parser.add_argument("--skip-plugins", action="store_true")
    args = parser.parse_args()

    entries = [make_entry(path, "personal") for path in skill_files(args.codex_skills, exclude_system=True)]
    entries += [make_entry(path, "shared") for path in skill_files(args.shared_skills)]
    plugins, enabled = ([], []) if args.skip_plugins else plugin_inventory()
    for plugin_name, plugin_path in enabled:
        for path in skill_files(plugin_path / "skills"):
            entries.append(make_entry(path, "official-plugin", plugin_name))

    entries.sort(key=lambda item: (item["invocation"], item["origin"], item["path"]))
    catalog = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skills": entries,
        "plugins": sorted(plugins, key=lambda item: (item["marketplace"], item["name"])),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "skills": len(entries),
        "implicit": sum(1 for item in entries if item["implicit_invocation"]),
        "explicit": sum(1 for item in entries if not item["implicit_invocation"]),
        "plugins_enabled": sum(1 for item in plugins if item["status"] == "installed-enabled"),
        "plugins_available": sum(1 for item in plugins if item["status"] == "not-installed"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
