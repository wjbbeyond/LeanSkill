#!/usr/bin/env python3
"""Deterministic first-pass router for LeanSkill."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROUTABLE = {"preferred", "available-explicit", "available-implicit"}

PREFERRED: dict[str, list[str]] = {
    "web-design": ["frontend-design", "product-design:index", "design-taste-frontend"],
    "web-implementation": ["build-web-apps:frontend-app-builder", "frontend-design"],
    "web-test": ["build-web-apps:frontend-testing-debugging", "browser:control-in-app-browser", "chrome:control-chrome"],
    "ios-implementation": ["build-ios-apps:swiftui-ui-patterns", "build-ios-apps:swiftui-view-refactor"],
    "ios-test": ["build-ios-apps:ios-simulator-browser", "build-ios-apps:ios-debugger-agent"],
    "game": ["game-studio:game-studio", "game-studio:phaser-2d-game", "game-studio:web-game-foundations"],
    "mobile-cross-platform": ["expo:expo-app"],
    "android": ["test-android-apps:android-app-testing"],
    "macos": ["build-macos-apps:swiftui-ui-patterns"],
    "backend": ["backend-architect", "api-design-principles", "database"],
    "ai-agent": ["openai-developers:agents-sdk", "cloudflare:agents-sdk", "backend-architect"],
    "security": ["security-audit", "productivity-skills:code-auditor", "code-reviewer"],
    "premium-visual": ["frontend-design", "design-taste-frontend", "high-end-visual-design"],
}

PLUGIN_GAPS = {
    "game": "game-studio@openai-curated",
    "mobile-cross-platform": "expo@openai-curated",
    "macos": "build-macos-apps@openai-curated",
    "android": "test-android-apps@openai-curated",
    "data-viz": "build-web-data-visualization@openai-curated",
    "design-source": "figma@openai-curated",
    "security": "codex-security@openai-curated",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def default_catalog() -> Path | None:
    candidates = [
        Path.home() / ".codex" / "leanskill" / "config.json",
        Path.home() / ".codex" / "skill-lab" / "config.json",
    ]
    for config in candidates:
        if config.exists():
            value = load_json(config).get("catalog_path")
            return Path(value).expanduser() if value else None
    return None


def text_files(project: Path) -> set[str]:
    try:
        return {p.name.lower() for p in project.iterdir()}
    except OSError:
        return set()


def read_packages(project: Path) -> str:
    paths = [project / "package.json"]
    paths += list(project.glob("apps/*/package.json"))
    paths += list(project.glob("packages/*/package.json"))
    contents = []
    for path in paths:
        if not path.exists():
            continue
        try:
            contents.append(path.read_text(encoding="utf-8").lower())
        except OSError:
            continue
    return "\n".join(contents)


def has_dependency(package_text: str, names: tuple[str, ...]) -> bool:
    return any(re.search(rf'"{re.escape(name)}"\s*:', package_text) for name in names)


def detect_project_type(project: Path, task: str = "") -> str:
    names = text_files(project)
    package = read_packages(project)
    task_value = task.lower()
    sample_paths = [str(p).lower() for p in list(project.glob("*"))[:200]] if project.exists() else []
    joined = " ".join(sample_paths)
    if has_dependency(package, ("phaser",)) or "cocos" in joined or "assets" in names and "settings" in names:
        return "game"
    if has_dependency(package, ("three", "@react-three/fiber", "babylonjs")):
        return "game"
    if has_dependency(package, ("expo", "react-native")):
        return "mobile-cross-platform"
    if any(name.endswith(".xcodeproj") or name.endswith(".xcworkspace") for name in names) or "package.swift" in names:
        return "ios"
    if "build.gradle" in names or "build.gradle.kts" in names:
        return "android"
    has_web = has_dependency(package, ("next", "react", "vue", "svelte", "vite", "astro"))
    ui_task = re.search(r"front.?end|\bui\b|\bux\b|interface|page|screen|前端|界面|页面|视觉", task_value)
    backend_task = re.search(r"backend|\bapi\b|database|worker|后端|接口|数据库", task_value)
    if has_web and ui_task:
        return "web"
    if backend_task and any(name in names for name in ("go.mod", "cargo.toml", "pyproject.toml", "requirements.txt")):
        return "backend"
    if has_web:
        return "web"
    if any(name in names for name in ("go.mod", "cargo.toml", "pyproject.toml", "requirements.txt")):
        return "backend"
    if "wrangler.toml" in names or "wrangler.jsonc" in names:
        return "backend"
    return "unknown"


def classify_task(task: str, requested_phase: str | None, requested_quality: str | None, requested_risk: str | None) -> tuple[str, str, str]:
    value = task.lower()
    phase = requested_phase or "implementation"
    phase_rules = [
        ("release", r"deploy|release|publish|上线|发布(?!前)"),
        ("security", r"security|auth|permission|secret|安全|鉴权|权限|密钥"),
        ("implementation", r"implement|develop|build|create|继续实现|继续开发|实现|开发|构建|创建"),
        ("performance", r"performance|latency|memory|性能|卡顿|延迟|内存"),
        ("test", r"test|debug|qa|verify|测试|调试|验收|验证"),
        ("architecture", r"architecture|schema|api design|架构|数据模型|接口设计|设计.*(?:api|数据库)|(?:api|数据库).*设计"),
        ("design", r"design|redesign|ui|ux|界面|视觉|美观|设计"),
        ("discovery", r"research|requirements|prototype|调研|需求|原型"),
    ]
    if requested_phase is None:
        for candidate, pattern in phase_rules:
            if re.search(pattern, value):
                phase = candidate
                break

    quality = requested_quality or ("premium-visual" if re.search(r"premium|beautiful|best-looking|高端|美观|最好看|视觉", value) else "production")
    high_risk = r"payment|production|migration|delete|publish|deploy|secret|auth|付费|生产|迁移|删除|发布|部署|密钥|鉴权"
    risk = requested_risk or ("high" if re.search(high_risk, value) else "medium" if phase in {"release", "security"} else "low")
    return phase, quality, risk


def index_catalog(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in data.get("skills", []):
        if item.get("status") not in ROUTABLE:
            continue
        for key in {item.get("invocation"), item.get("name")}:
            if key and key not in result:
                result[str(key)] = item
    return result


def first_available(index: dict[str, dict[str, Any]], names: list[str], excluded: set[str]) -> dict[str, Any] | None:
    for name in names:
        item = index.get(name)
        if item and item.get("invocation") not in excluded:
            return item
    return None


def build_route(project: Path, task: str, data: dict[str, Any], phase: str | None, quality: str | None, risk: str | None) -> dict[str, Any]:
    project_type = detect_project_type(project, task)
    phase, quality, risk = classify_task(task, phase, quality, risk)
    index = index_catalog(data)

    task_value = task.lower()
    ui_task = re.search(r"front.?end|\bui\b|\bux\b|interface|page|screen|前端|界面|页面|视觉", task_value)
    ai_task = re.search(r"ai agent|agent|llm|model|大模型|智能体|ai 生成|ai生成", task_value)
    if ai_task and not ui_task:
        route_key = "ai-agent"
    elif project_type == "web":
        route_key = "web-design" if phase in {"discovery", "design"} else "web-test" if phase == "test" else "web-implementation"
    elif project_type == "ios":
        route_key = "ios-test" if phase == "test" else "ios-implementation"
    elif project_type == "game":
        route_key = "game"
    elif project_type in {"mobile-cross-platform", "android", "macos"}:
        route_key = project_type
    else:
        route_key = "backend"

    primary = first_available(index, PREFERRED[route_key], set())
    specialists: list[dict[str, Any]] = []

    specialist_lists: list[list[str]] = []
    if quality == "premium-visual" and project_type in {"web", "mobile-cross-platform"}:
        specialist_lists.append(PREFERRED["premium-visual"])
    if phase == "test" and project_type == "web":
        specialist_lists.append(PREFERRED["web-test"])
    if risk == "high" or phase == "security":
        specialist_lists.append(PREFERRED["security"])

    used = {primary.get("invocation")} if primary else set()
    for choices in specialist_lists:
        if len(specialists) >= 2:
            break
        item = first_available(index, choices, used)
        if item:
            specialists.append(item)
            used.add(item.get("invocation"))

    gaps: list[dict[str, str]] = []
    plugin_key = project_type if project_type in PLUGIN_GAPS else None
    if primary is None and plugin_key:
        gaps.append({"capability": plugin_key, "candidate_plugin": PLUGIN_GAPS[plugin_key], "action": "research-only; approval-required"})
    elif primary is None:
        gaps.append({"capability": route_key, "action": "use-native-codex-and-log-gap"})

    gates = ["project-instructions", "proportional-tests"]
    if quality == "premium-visual":
        gates += ["visual-target", "responsive-or-size-class-evidence", "real-render-review"]
    if risk == "high":
        gates += ["explicit-authority", "bounded-impact", "rollback"]

    return {
        "profile": {"project_type": project_type, "phase": phase, "quality": quality, "risk": risk},
        "primary": primary.get("invocation") if primary else None,
        "specialists": [item.get("invocation") for item in specialists],
        "selected_count": (1 if primary else 0) + len(specialists),
        "gates": gates,
        "gaps": gaps,
        "rules": {"max_selected": 3, "auto_install": False, "reroute_at_checkpoints_only": True},
    }


def to_markdown(route: dict[str, Any]) -> str:
    profile = route["profile"]
    specialists = ", ".join(route["specialists"]) or "none"
    gaps = "; ".join(gap["capability"] for gap in route["gaps"]) or "none"
    return "\n".join([
        "## Route receipt",
        f"- Profile: {profile['project_type']} / {profile['phase']} / {profile['quality']} / {profile['risk']}",
        f"- Primary: {route['primary'] or 'native Codex'}",
        f"- Specialists: {specialists}",
        f"- Gates: {', '.join(route['gates'])}",
        f"- Gaps: {gaps}",
        "- New installs: forbidden without approval",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--phase")
    parser.add_argument("--quality")
    parser.add_argument("--risk")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    catalog = args.catalog or default_catalog()
    data = load_json(catalog) if catalog and catalog.exists() else {"skills": []}
    route = build_route(args.project.resolve(), args.task, data, args.phase, args.quality, args.risk)
    print(to_markdown(route) if args.format == "markdown" else json.dumps(route, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
