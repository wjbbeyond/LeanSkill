#!/usr/bin/env python3
"""Deterministic, evidence-aware first-pass router for LeanSkill."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROUTABLE = {"preferred", "available-explicit", "available-implicit"}
ROUTING_BUDGET = {
    "pre_route_command_batches": 5,
    "receipt_before_deep_inspection": True,
    "tests_before_receipt": False,
    "broad_scan_before_receipt": False,
}
DEFAULT_PLAN_PATH = Path("docs/LEANSKILL_PLAN.md")

PREFERRED: dict[str, list[str]] = {
    "web-design": ["frontend-design", "product-design:index", "design-taste-frontend"],
    "web-implementation": [
        "build-web-apps:frontend-app-builder",
        "frontend-design",
    ],
    "web-quality": [
        "build-web-apps:react-best-practices",
        "vercel:react-best-practices",
    ],
    "web-test": [
        "build-web-apps:frontend-testing-debugging",
        "browser:control-in-app-browser",
        "chrome:control-chrome",
    ],
    "ios-implementation": ["build-ios-apps:swiftui-ui-patterns", "build-ios-apps:swiftui-view-refactor"],
    "ios-test": ["build-ios-apps:ios-simulator-browser", "build-ios-apps:ios-debugger-agent"],
    "game": ["game-studio:game-studio", "game-studio:phaser-2d-game", "game-studio:web-game-foundations"],
    "mobile-cross-platform": ["expo:expo-app"],
    "android": ["test-android-apps:android-app-testing"],
    "macos": ["build-macos-apps:swiftui-ui-patterns"],
    "backend": ["backend-architect", "api-design-principles", "database"],
    "ai-agent": ["openai-developers:agents-sdk", "cloudflare:agents-sdk", "backend-architect"],
    "developer-tooling": ["skill-creator", "plugin-creator", "code-reviewer"],
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

TRUST_POINTS = {
    "official-system": 20,
    "official-plugin": 20,
    "local-system": 18,
    "reviewed-local": 15,
    "community-local": 10,
    "local-unverified": 5,
}
STATUS_POINTS = {"preferred": 10, "available-implicit": 8, "available-explicit": 6}
POSITIVE_OUTCOMES = {"success", "local-success", "local-success-external-blocked"}
PARTIAL_OUTCOMES = {"partial"}
NEGATIVE_OUTCOMES = {"failure"}

ENGLISH_ACTIONS = (
    r"install(?:ing)?|enable|download|execute|deploy(?:ing)?|release|publish(?:ing)?|"
    r"migrate|migration|delete|spend|use production data|using production data|"
    r"write to production|call paid api|paid api calls?"
)
CHINESE_ACTIONS = (
    r"安装|启用|下载|执行|部署|发布|上线|迁移|删除|付费调用|调用付费\s*API|"
    r"使用生产\s*数据|写入生产\s*环境|操作生产\s*环境"
)
ENGLISH_NEGATION = re.compile(
    rf"\b(?:do\s+not|don't|must\s+not|without|never|no)\s+"
    rf"(?:{ENGLISH_ACTIONS})(?:(?:\s*(?:,|/|and|or)\s*)(?:{ENGLISH_ACTIONS}))*",
    re.IGNORECASE,
)
CHINESE_NEGATION = re.compile(
    rf"(?:不|不要|无需|禁止|不得|未授权|不会|不执行|不进行|不使用|不调用)\s*"
    rf"(?:{CHINESE_ACTIONS})(?:(?:[、，,/与和或\s]*)(?:{CHINESE_ACTIONS}))*",
    re.IGNORECASE,
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def default_config() -> dict[str, Any]:
    candidates = [
        Path.home() / ".codex" / "leanskill" / "config.json",
        Path.home() / ".codex" / "skill-lab" / "config.json",
    ]
    for config in candidates:
        if config.exists():
            return load_json(config)
    return {}


def default_catalog() -> Path | None:
    value = default_config().get("catalog_path")
    return Path(value).expanduser() if value else None


def default_feedback() -> Path | None:
    config = default_config()
    value = config.get("feedback_path")
    if value:
        return Path(value).expanduser()
    root = config.get("lab_root")
    return Path(root).expanduser() / "state" / "outcomes.jsonl" if root else None


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


def has_skill_markers(project: Path) -> bool:
    if (project / "SKILL.md").is_file():
        return True
    return any(project.glob("skills/*/SKILL.md"))


def detect_project_type(project: Path, task: str = "") -> str:
    names = text_files(project)
    package = read_packages(project)
    task_value = task.lower()
    sample_paths = [str(p).lower() for p in list(project.glob("*"))[:200]] if project.exists() else []
    joined = " ".join(sample_paths)
    explicit_skill_task = re.search(
        r"codex\s+(?:skill|plugin)|(?:create|update|improve|maintain|test).{0,24}(?:skill|plugin|router)|"
        r"(?:创建|更新|改进|维护|测试).{0,24}(?:skill|插件|路由器)|leanskill|技能路由",
        task_value,
    )
    if explicit_skill_task and (has_skill_markers(project) or "codex" in task_value or "leanskill" in task_value):
        return "developer-tooling"
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


def strip_negated_actions(task: str) -> tuple[str, list[str]]:
    matches: list[str] = []

    def replace(match: re.Match[str]) -> str:
        matches.append(match.group(0).strip())
        return " "

    value = ENGLISH_NEGATION.sub(replace, task)
    value = CHINESE_NEGATION.sub(replace, value)
    return value, matches


def classify_task(
    task: str,
    requested_phase: str | None,
    requested_quality: str | None,
    requested_risk: str | None,
) -> tuple[str, str, str]:
    normalized, _ = strip_negated_actions(task)
    value = normalized.lower()
    phase = requested_phase or "implementation"
    phase_rules = [
        ("release", r"deploy|release|publish|上线|发布(?!前)|部署"),
        ("security", r"security|auth|permission|secret|安全|鉴权|权限|密钥"),
        ("maintenance", r"maintain|upgrade|refactor|update existing|维护|升级|重构|改进现有|更新现有"),
        ("implementation", r"implement|develop|build|create|继续实现|继续开发|实现|开发|构建|创建"),
        ("performance", r"performance|latency|memory|性能|卡顿|延迟|内存"),
        ("test", r"test|debug|qa|verify|测试|调试|验收|验证|修复"),
        ("architecture", r"architecture|schema|api design|架构|数据模型|接口设计|设计.*(?:api|数据库)|(?:api|数据库).*设计"),
        ("design", r"design|redesign|ui|ux|界面|视觉|美观|设计"),
        ("discovery", r"research|requirements|prototype|调研|需求|原型"),
    ]
    if requested_phase is None:
        for candidate, pattern in phase_rules:
            if re.search(pattern, value):
                phase = candidate
                break

    quality = requested_quality or (
        "premium-visual" if re.search(r"premium|beautiful|best-looking|高端|美观|最好看|视觉", value) else "production"
    )
    high_risk = (
        r"payment|stripe|production\s+(?:data|environment|write)|database\s+migration|"
        r"delete|publish|deploy|secret|auth|付费|生产数据|生产环境|线上环境|迁移|删除|发布|部署|密钥|鉴权"
    )
    risk = requested_risk or (
        "high" if re.search(high_risk, value) else "medium" if phase in {"release", "security"} else "low"
    )
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


def feedback_for(
    outcomes: list[dict[str, Any]],
    invocation: str,
    profile: dict[str, str],
) -> list[dict[str, Any]]:
    matches = []
    for record in outcomes:
        record_profile = record.get("profile", {})
        route = record.get("route", {})
        selected = [route.get("primary"), *route.get("specialists", [])]
        if invocation not in selected:
            continue
        if record_profile.get("project_type") != profile["project_type"]:
            continue
        if record_profile.get("phase") != profile["phase"]:
            continue
        matches.append(record)
    return matches


def outcome_signal(record: dict[str, Any]) -> float:
    status = record.get("outcome", {}).get("status")
    if status in POSITIVE_OUTCOMES:
        return 1.0
    if status in PARTIAL_OUTCOMES:
        return 0.5
    if status in NEGATIVE_OUTCOMES:
        return -1.0
    return 0.0


def value_detail(
    item: dict[str, Any],
    preference_rank: int,
    outcomes: list[dict[str, Any]],
    profile: dict[str, str],
    role: str,
) -> dict[str, Any]:
    invocation = str(item.get("invocation"))
    fit = max(18, 40 - 7 * preference_rank)
    trust = TRUST_POINTS.get(str(item.get("trust_tier")), 4)
    readiness = STATUS_POINTS.get(str(item.get("status")), 0)
    matches = feedback_for(outcomes, invocation, profile)
    count = len(matches)
    evidence_limit = min(15, 3 + 3 * count) if count else 0
    average_signal = sum(outcome_signal(record) for record in matches) / count if count else 0.0
    measured_outcome = round(max(-1.0, min(1.0, average_signal)) * evidence_limit)

    token_values = [record.get("outcome", {}).get("token_efficiency", "unknown") for record in matches]
    token_measured = [value for value in token_values if value in {"better", "neutral", "worse"}]
    efficiency = 0
    if token_measured:
        mapping = {"better": 5, "neutral": 0, "worse": -5}
        efficiency += round(sum(mapping[value] for value in token_measured) / len(token_measured))
    value_profile = item.get("value_profile", {})
    efficiency += {"low": 3, "medium": 0, "high": -3}.get(value_profile.get("context_cost"), 0)
    efficiency += {"low": 2, "medium": 0, "high": -3}.get(value_profile.get("native_overlap"), 0)
    efficiency = max(-10, min(10, efficiency))
    durability = {"current": 5, "unknown": 0, "stale": -5}.get(value_profile.get("maintenance"), 0)
    score = max(0, min(100, fit + trust + readiness + measured_outcome + efficiency + durability))

    failures = sum(1 for record in matches if record.get("outcome", {}).get("status") in NEGATIVE_OUTCOMES)
    worse = sum(1 for value in token_values if value == "worse")
    negative_optimization = count >= 3 and failures * 2 >= count and worse * 2 >= count
    confidence = "high" if count >= 3 and token_measured else "medium" if count else "low"
    native_comparison = "unknown"
    if token_measured:
        average = sum({"better": 1, "neutral": 0, "worse": -1}[value] for value in token_measured) / len(token_measured)
        native_comparison = "better" if average > 0.25 else "worse" if average < -0.25 else "neutral"

    reasons = [
        f"route-fit rank {preference_rank + 1}",
        f"trust {item.get('trust_tier', 'unknown')}",
        f"availability {item.get('status', 'unknown')}",
    ]
    if count:
        reasons.append(f"{count} matching local outcome{'s' if count != 1 else ''}")
    else:
        reasons.append("no matching local outcomes yet")
    if not token_measured:
        reasons.append("native/token comparison unknown")
    if negative_optimization:
        reasons.append("observed negative optimization")

    return {
        "invocation": invocation,
        "role": role,
        "decision_score": score,
        "confidence": confidence,
        "matching_outcomes": count,
        "native_comparison": native_comparison,
        "negative_optimization": negative_optimization,
        "reasons": reasons,
    }


def ranked_available(
    index: dict[str, dict[str, Any]],
    names: list[str],
    excluded: set[str],
    outcomes: list[dict[str, Any]],
    profile: dict[str, str],
    role: str,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    ranked: list[tuple[int, dict[str, Any], dict[str, Any]]] = []
    seen: set[str] = set()
    for preference_rank, name in enumerate(names):
        item = index.get(name)
        if not item:
            continue
        invocation = str(item.get("invocation"))
        if invocation in excluded or invocation in seen:
            continue
        seen.add(invocation)
        detail = value_detail(item, preference_rank, outcomes, profile, role)
        ranked.append((preference_rank, item, detail))
    ranked.sort(key=lambda row: (-row[2]["decision_score"], row[0], row[2]["invocation"]))
    return [(item, detail) for _, item, detail in ranked]


def build_route(
    project: Path,
    task: str,
    data: dict[str, Any],
    phase: str | None,
    quality: str | None,
    risk: str | None,
    outcomes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    outcomes = outcomes or []
    project_type = detect_project_type(project, task)
    phase, quality, risk = classify_task(task, phase, quality, risk)
    profile = {"project_type": project_type, "phase": phase, "quality": quality, "risk": risk}
    index = index_catalog(data)
    normalized_task, negated_actions = strip_negated_actions(task)
    task_value = normalized_task.lower()
    ui_task = re.search(r"front.?end|\bui\b|\bux\b|interface|page|screen|前端|界面|页面|视觉", task_value)
    ai_task = re.search(r"ai agent|agent|llm|model|大模型|智能体|ai 生成|ai生成", task_value)
    package = read_packages(project)
    is_react = has_dependency(package, ("react", "next"))

    if project_type == "developer-tooling":
        route_key = "developer-tooling"
    elif ai_task and not ui_task:
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

    primary_ranked = ranked_available(index, PREFERRED[route_key], set(), outcomes, profile, "primary")
    primary_item: dict[str, Any] | None = None
    primary_detail: dict[str, Any] | None = None
    for item, detail in primary_ranked:
        if not detail["negative_optimization"]:
            primary_item, primary_detail = item, detail
            break

    specialist_lists: list[list[str]] = []
    if risk == "high" or phase == "security":
        specialist_lists.append(PREFERRED["security"])
    if quality == "premium-visual" and project_type in {"web", "mobile-cross-platform"}:
        specialist_lists.append(PREFERRED["premium-visual"])
    if phase == "test" and project_type == "web":
        specialist_lists.append(PREFERRED["web-test"])
    if is_react and phase in {"implementation", "maintenance", "test", "performance"}:
        specialist_lists.append(PREFERRED["web-quality"])

    used = {str(primary_item.get("invocation"))} if primary_item else set()
    specialist_details: list[dict[str, Any]] = []
    for choices in specialist_lists:
        if len(specialist_details) >= 2:
            break
        ranked = ranked_available(index, choices, used, outcomes, profile, "specialist")
        selected = next(((item, detail) for item, detail in ranked if not detail["negative_optimization"]), None)
        if selected:
            item, detail = selected
            specialist_details.append(detail)
            used.add(str(item.get("invocation")))

    primary = str(primary_item.get("invocation")) if primary_item else None
    specialists = [detail["invocation"] for detail in specialist_details]
    selection = ([primary_detail] if primary_detail else []) + specialist_details
    selected_invocations = {item["invocation"] for item in selection}
    matching_route_outcomes = sum(
        1
        for record in outcomes
        if record.get("profile", {}).get("project_type") == profile["project_type"]
        and record.get("profile", {}).get("phase") == profile["phase"]
        and selected_invocations.intersection(
            {record.get("route", {}).get("primary"), *record.get("route", {}).get("specialists", [])}
        )
    )
    gaps: list[dict[str, str]] = []
    available_but_negative = bool(primary_ranked) and primary is None
    plugin_key = project_type if project_type in PLUGIN_GAPS else None
    if available_but_negative:
        gaps.append({"capability": route_key, "action": "use-native-codex-observed-negative-value"})
    elif primary is None and plugin_key:
        gaps.append({"capability": plugin_key, "candidate_plugin": PLUGIN_GAPS[plugin_key], "action": "research-only; approval-required"})
    elif primary is None:
        gaps.append({"capability": route_key, "action": "use-native-codex-and-log-gap"})

    gates = ["project-instructions", "proportional-tests"]
    if quality == "premium-visual":
        gates += ["visual-target", "responsive-or-size-class-evidence", "real-render-review"]
    if risk == "high":
        gates += ["explicit-authority", "bounded-impact", "rollback"]

    alternatives = [detail for _, detail in primary_ranked if detail["invocation"] != primary][:2]
    return {
        "profile": profile,
        "primary": primary,
        "specialists": specialists,
        "selection": selection,
        "alternatives": alternatives,
        "selected_count": (1 if primary else 0) + len(specialists),
        "gates": gates,
        "gaps": gaps,
        "classification": {"ignored_negated_constraints": negated_actions},
        "value_evidence": {"matching_route_outcomes": matching_route_outcomes},
        "rules": {
            "max_selected": 3,
            "auto_install": False,
            "routing_mode": "plan-once",
            "automatic_reroute": False,
            "reroute_requires_explicit_user_request": True,
            "post_plan_owner": "native-codex",
            "transitive_skills_count_toward_limit": True,
            "value_scoring": "evidence-aware-v1",
            "unknown_metrics_reduce_confidence": True,
            **ROUTING_BUDGET,
        },
    }


def to_markdown(route: dict[str, Any]) -> str:
    profile = route["profile"]
    primary_detail = next((item for item in route["selection"] if item["role"] == "primary"), None)
    if primary_detail:
        primary = (
            f"{primary_detail['invocation']} "
            f"(decision {primary_detail['decision_score']}/100; confidence {primary_detail['confidence']})"
        )
    else:
        primary = "native Codex"
    specialist_text = ", ".join(
        f"{item['invocation']} ({item['decision_score']}/100; {item['confidence']})"
        for item in route["selection"]
        if item["role"] == "specialist"
    ) or "none"
    alternatives = ", ".join(
        f"{item['invocation']} ({item['decision_score']}/100)" for item in route["alternatives"]
    ) or "none"
    gaps = "; ".join(gap["capability"] for gap in route["gaps"]) or "none"
    outcome_count = route["value_evidence"]["matching_route_outcomes"]
    lines = [
        "## Route receipt",
        "- Mode: Plan Once, Execute Native",
        f"- Profile: {profile['project_type']} / {profile['phase']} / {profile['quality']} / {profile['risk']}",
        f"- Primary: {primary}",
        f"- Specialists: {specialist_text}",
        f"- Alternatives considered: {alternatives}",
        f"- Local value evidence: {outcome_count} matching outcome record(s); unknown metrics lower confidence",
        f"- Gates: {', '.join(route['gates'])}",
        f"- Gaps: {gaps}",
        f"- Pre-route budget: <= {route['rules']['pre_route_command_batches']} read-only command batches; no broad scan or tests before receipt",
        "- New installs: forbidden without approval",
        "- Handoff: native Codex owns execution; LeanSkill does not re-run automatically",
    ]
    if route.get("artifact", {}).get("plan"):
        lines.append(f"- Saved plan: {route['artifact']['plan']}")
    return "\n".join(lines)


def to_plan_markdown(route: dict[str, Any]) -> str:
    profile = route["profile"]
    selection = route["selection"]
    primary = next((item for item in selection if item["role"] == "primary"), None)
    specialists = [item for item in selection if item["role"] == "specialist"]
    gaps = route["gaps"]

    lines = [
        "# LeanSkill Initial Capability Plan",
        "",
        "> Mode: Plan Once, Execute Native. This is an advisory starting plan, not a permanent Skill whitelist.",
        "",
        "## Detected profile",
        "",
        f"- Project type: {profile['project_type']}",
        f"- Initial phase: {profile['phase']}",
        f"- Quality target: {profile['quality']}",
        f"- Risk/cost: {profile['risk']}",
        "",
        "## Advisory shortlist",
        "",
    ]
    if primary:
        lines.append(
            f"- Primary: `{primary['invocation']}` — decision {primary['decision_score']}/100; "
            f"confidence {primary['confidence']}; {'; '.join(primary['reasons'])}."
        )
    else:
        lines.append("- Primary: native Codex — no numeric score is assigned.")
    if specialists:
        for item in specialists:
            lines.append(
                f"- Specialist: `{item['invocation']}` — decision {item['decision_score']}/100; "
                f"confidence {item['confidence']}; {'; '.join(item['reasons'])}."
            )
    else:
        lines.append("- Specialists: none.")

    lines += [
        "",
        "## Gates and gaps",
        "",
        f"- Initial gates: {', '.join(route['gates'])}",
    ]
    if gaps:
        for gap in gaps:
            details = "; ".join(f"{key}={value}" for key, value in gap.items())
            lines.append(f"- Gap: {details}")
    else:
        lines.append("- Gaps: none detected by the initial route.")

    lines += [
        "",
        "## Execution handoff",
        "",
        "- Native Codex owns implementation, testing, debugging, and later capability choices.",
        "- The shortlist is not preloaded and does not prohibit direct use of another installed Skill when it adds concrete value.",
        "- Native Codex may use an installed explicit-only Skill by its exact invocation name; this is direct Skill use, not LeanSkill re-routing.",
        "- Any transitive Skill dependency must be disclosed and counts toward the three-capability planning limit.",
        "- LeanSkill does not re-run at phase changes, gate failures, or scope changes.",
        "- Re-run LeanSkill only when the user explicitly requests capability re-planning.",
        "- Never install, enable, download, or execute a newly discovered Skill or plugin without explicit user approval.",
        "",
    ]
    return "\n".join(lines)


def resolve_plan_path(project: Path, requested: Path) -> Path:
    project_root = project.resolve()
    candidate = requested if requested.is_absolute() else project_root / requested
    resolved = candidate.resolve()
    try:
        resolved.relative_to(project_root)
    except ValueError as error:
        raise ValueError("plan path must stay inside the project root") from error
    if resolved == project_root or resolved.suffix.lower() != ".md":
        raise ValueError("plan path must be a Markdown file inside the project root")
    return resolved


def write_plan(project: Path, requested: Path, route: dict[str, Any], force: bool = False) -> Path:
    target = resolve_plan_path(project, requested)
    target.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if force else "x"
    try:
        with target.open(mode, encoding="utf-8") as handle:
            handle.write(to_plan_markdown(route))
    except FileExistsError as error:
        raise ValueError("plan already exists; use --force-plan only for an explicit user-requested re-route") from error
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--feedback", type=Path)
    parser.add_argument("--phase")
    parser.add_argument("--quality")
    parser.add_argument("--risk")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument(
        "--write-plan",
        nargs="?",
        const=DEFAULT_PLAN_PATH,
        type=Path,
        help="write an advisory project plan (default: docs/LEANSKILL_PLAN.md)",
    )
    parser.add_argument("--force-plan", action="store_true", help="replace an existing plan after explicit user-requested re-routing")
    args = parser.parse_args()

    if args.force_plan and args.write_plan is None:
        parser.error("--force-plan requires --write-plan")

    catalog = args.catalog or default_catalog()
    feedback = args.feedback or default_feedback()
    data = load_json(catalog) if catalog and catalog.exists() else {"skills": []}
    outcomes = load_jsonl(feedback)
    project = args.project.resolve()
    if not project.is_dir():
        parser.error("--project must be an existing directory")
    route = build_route(project, args.task, data, args.phase, args.quality, args.risk, outcomes)
    if args.write_plan is not None:
        try:
            plan = write_plan(project, args.write_plan, route, args.force_plan)
        except ValueError as error:
            parser.error(str(error))
        route["artifact"] = {"plan": str(plan.relative_to(project))}
    print(to_markdown(route) if args.format == "markdown" else json.dumps(route, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
