#!/usr/bin/env python3
"""Install, inspect, upgrade, or uninstall LeanSkill without hidden mutations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.2.0-beta"
START_MARKER = "<!-- LEANSKILL:START -->"
END_MARKER = "<!-- LEANSKILL:END -->"
AGENTS_BLOCK = """<!-- LEANSKILL:START -->
# LeanSkill capability routing

Use `$leanskill-router` exactly once before substantial implementation when planning a genuinely new software, app, website, game, or AI project. Run its deterministic helper with `--write-plan` and emit the generated route receipt verbatim; never invent or adjust scores. If `docs/LEANSKILL_PLAN.md` already exists, do not re-run LeanSkill unless the user explicitly requests re-planning.

Do not use LeanSkill automatically for an existing project, a feature in an existing project, implementation continuation, a phase change, a failed gate, Q&A, status, diagnosis, research, API/provider selection, or a routine edit. Re-run it only when the user explicitly asks for `$leanskill-router` or capability re-planning.

After the initial plan, native Codex owns execution and directly chooses installed specialist Skills when they add concrete value. It may explicitly invoke an installed explicit-only Skill by its exact invocation name when the saved plan or current task supplies concrete evidence; this is direct Skill use, not LeanSkill re-routing. Consult `docs/LEANSKILL_PLAN.md` as advisory context during project orientation; do not preload its shortlist or treat it as a whitelist. Count transitive Skill dependencies toward the one-primary-plus-two-specialists planning limit. Never install, enable, download, or execute a new skill or plugin without explicit user approval.

For user-facing UI, native Codex must establish a visual target and design tokens before implementation, then verify the real rendered surface in a browser or simulator. Do not deploy, publish, spend money, use production data, or mutate external systems without user authority.
<!-- LEANSKILL:END -->"""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_path(path: Path) -> str | None:
    if not path.exists():
        return None
    if path.is_file():
        return sha256_bytes(path.read_bytes())
    digest = hashlib.sha256()
    for file in sorted(item for item in path.rglob("*") if item.is_file() and "__pycache__" not in item.parts and file_suffix_ok(item)):
        digest.update(str(file.relative_to(path)).encode("utf-8"))
        digest.update(b"\0")
        digest.update(file.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def file_suffix_ok(path: Path) -> bool:
    return path.suffix != ".pyc"


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def atomic_copy_tree(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{target.name}-", dir=target.parent))
    shutil.rmtree(temporary)
    shutil.copytree(source, temporary, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    displaced: Path | None = None
    try:
        if target.exists():
            displaced = target.with_name(f".{target.name}-old-{os.getpid()}")
            os.replace(target, displaced)
        os.replace(temporary, target)
        if displaced:
            shutil.rmtree(displaced)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        if displaced and displaced.exists() and not target.exists():
            os.replace(displaced, target)
        raise


def replace_agents_block(original: str) -> str:
    pattern = re.compile(rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}", re.DOTALL)
    if pattern.search(original):
        return pattern.sub(AGENTS_BLOCK, original, count=1)
    if (
        original.lstrip().startswith("# Global project capability routing")
        and "$project-dev-router" in original
        and "CodexSkillLab catalog" in original
    ):
        return AGENTS_BLOCK + "\n"
    separator = "" if not original else "\n" if original.endswith("\n") else "\n\n"
    return original + separator + AGENTS_BLOCK + "\n"


def remove_agents_block(original: str) -> tuple[str, bool]:
    pattern = re.compile(rf"\n?{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}\n?", re.DOTALL)
    if not pattern.search(original):
        return original, False
    updated = pattern.sub("\n", original, count=1).strip("\n")
    return (updated + "\n" if updated else ""), True


def backup_item(source: Path, target: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def paths(args: argparse.Namespace) -> dict[str, Path]:
    codex_home = args.codex_home.expanduser().resolve()
    repo_root = args.repo_root.expanduser().resolve()
    global_agents = (args.global_agents or codex_home / "AGENTS.md").expanduser().resolve()
    state_root = codex_home / "leanskill"
    return {
        "codex_home": codex_home,
        "repo_root": repo_root,
        "source_skill": repo_root / "skills" / "leanskill-router",
        "skill_target": codex_home / "skills" / "leanskill-router",
        "global_agents": global_agents,
        "state_root": state_root,
        "config": state_root / "config.json",
        "manifest": state_root / "install-manifest.json",
        "shared_skills": args.shared_skills.expanduser().resolve(),
        "legacy_policy": codex_home / "skills" / "project-dev-router" / "agents" / "openai.yaml",
    }


def planned_actions(p: dict[str, Path], command: str) -> dict[str, Any]:
    return {
        "command": command,
        "version": VERSION,
        "repo_root": str(p["repo_root"]),
        "skill": str(p["skill_target"]),
        "global_agents": str(p["global_agents"]),
        "config": str(p["config"]),
        "manifest": str(p["manifest"]),
        "legacy_router_detected": is_legacy_router(p["legacy_policy"]),
    }


def is_legacy_router(policy_path: Path) -> bool:
    skill = policy_path.parents[1] / "SKILL.md"
    if not skill.is_file():
        return False
    text = skill.read_text(encoding="utf-8", errors="replace")
    return "name: project-dev-router" in text and "CodexSkillLab" in text and "# Project Dev Router" in text


def set_legacy_explicit_only(policy_path: Path) -> bool:
    if not is_legacy_router(policy_path):
        return False
    original = policy_path.read_text(encoding="utf-8", errors="strict") if policy_path.exists() else ""
    pattern = re.compile(r"^(\s*allow_implicit_invocation\s*:\s*)(true|false)(\s*)$", re.MULTILINE | re.IGNORECASE)
    if pattern.search(original):
        updated = pattern.sub(lambda match: match.group(1) + "false" + match.group(3), original, count=1)
    elif re.search(r"^policy\s*:\s*$", original, re.MULTILINE):
        match = re.search(r"^policy\s*:\s*$", original, re.MULTILINE)
        assert match is not None
        updated = original[:match.end()] + "\n  allow_implicit_invocation: false" + original[match.end():]
    else:
        separator = "" if not original or original.endswith("\n") else "\n"
        updated = original + separator + "policy:\n  allow_implicit_invocation: false\n"
    atomic_write(policy_path, updated.encode("utf-8"))
    return True


def build_catalog(p: dict[str, Path]) -> None:
    script = p["repo_root"] / "scripts" / "build_catalog.py"
    output = p["repo_root"] / "catalog" / "registry.json"
    command = [
        sys.executable,
        str(script),
        "--output",
        str(output),
        "--codex-skills",
        str(p["codex_home"] / "skills"),
        "--shared-skills",
        str(p["shared_skills"]),
    ]
    if p["skip_plugins"]:
        command.append("--skip-plugins")
    process = subprocess.run(command, check=False, text=True, capture_output=True)
    if process.returncode:
        raise RuntimeError(f"catalog build failed: {process.stderr.strip() or process.stdout.strip()}")


def ensure_local_templates(repo_root: Path) -> None:
    catalog = repo_root / "catalog"
    for name in ("candidates", "verified", "rejected", "gaps"):
        target = catalog / f"{name}.json"
        source = catalog / f"{name}.example.json"
        if not target.exists():
            shutil.copy2(source, target)


def initial_manifest(p: dict[str, Path]) -> dict[str, Any]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = p["codex_home"] / "backups" / f"leanskill-install-{stamp}"
    backup_root.mkdir(parents=True, exist_ok=False)
    originals: dict[str, Any] = {}
    for key in ("skill_target", "global_agents", "config", "legacy_policy"):
        source = p[key]
        existed = source.exists()
        backup = backup_root / key
        if existed:
            backup_item(source, backup)
        originals[key] = {
            "path": str(source),
            "existed": existed,
            "hash": hash_path(source),
            "backup": str(backup) if existed else None,
        }
    return {
        "schema_version": 1,
        "version": VERSION,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(p["repo_root"]),
        "backup_root": str(backup_root),
        "originals": originals,
        "managed": {},
    }


def verify_managed(manifest: dict[str, Any], p: dict[str, Path], force: bool) -> None:
    conflicts = []
    keys = ["skill_target", "config"]
    if manifest.get("legacy_migrated"):
        keys.append("legacy_policy")
    for key in keys:
        expected = manifest.get("managed", {}).get(key)
        current = hash_path(p[key])
        if expected is not None and current != expected:
            conflicts.append(key)
    agents = p["global_agents"]
    if agents.exists():
        content = agents.read_text(encoding="utf-8", errors="replace")
        if START_MARKER not in content or END_MARKER not in content:
            conflicts.append("global_agents_marker")
    if conflicts and not force:
        raise RuntimeError(f"managed files changed: {', '.join(conflicts)}; inspect them or rerun with --force")


def install(args: argparse.Namespace, p: dict[str, Path]) -> int:
    if not (p["source_skill"] / "SKILL.md").is_file():
        raise RuntimeError(f"missing source skill: {p['source_skill']}")
    if args.dry_run:
        print(json.dumps({**planned_actions(p, "install"), "dry_run": True}, ensure_ascii=False, indent=2))
        return 0

    ensure_local_templates(p["repo_root"])
    build_catalog(p)
    existing = p["manifest"].exists()
    manifest = json.loads(p["manifest"].read_text(encoding="utf-8")) if existing else initial_manifest(p)
    if existing:
        verify_managed(manifest, p, args.force)
    previous_config = json.loads(p["config"].read_text(encoding="utf-8")) if p["config"].is_file() else {}

    atomic_copy_tree(p["source_skill"], p["skill_target"])
    agents_original = p["global_agents"].read_text(encoding="utf-8", errors="strict") if p["global_agents"].exists() else ""
    atomic_write(p["global_agents"], replace_agents_block(agents_original).encode("utf-8"))
    config = {
        "schema_version": 1,
        "routing_mode": "plan-once",
        "lab_root": str(p["repo_root"]),
        "catalog_path": str(p["repo_root"] / "catalog" / "registry.json"),
        "feedback_path": str(p["repo_root"] / "state" / "outcomes.jsonl"),
        "record_outcomes": bool(args.record_outcomes or previous_config.get("record_outcomes", False)),
    }
    atomic_write(p["config"], (json.dumps(config, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    legacy_migrated = set_legacy_explicit_only(p["legacy_policy"])

    manifest.update(version=VERSION, installed_at=datetime.now(timezone.utc).isoformat(), repo_root=str(p["repo_root"]))
    manifest["legacy_migrated"] = legacy_migrated or bool(manifest.get("legacy_migrated"))
    manifest["managed"] = {
        "skill_target": hash_path(p["skill_target"]),
        "global_agents": hash_path(p["global_agents"]),
        "config": hash_path(p["config"]),
    }
    if manifest["legacy_migrated"]:
        manifest["managed"]["legacy_policy"] = hash_path(p["legacy_policy"])
    atomic_write(p["manifest"], (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({**planned_actions(p, "upgrade" if existing else "install"), "installed": True}, ensure_ascii=False, indent=2))
    return 0


def restore_original(key: str, p: dict[str, Path], manifest: dict[str, Any], conflicts: list[str]) -> None:
    target = p[key]
    expected = manifest.get("managed", {}).get(key)
    if hash_path(target) != expected:
        conflicts.append(key)
        return
    original = manifest["originals"][key]
    if target.exists():
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    if original["existed"]:
        backup_item(Path(original["backup"]), target)


def uninstall(args: argparse.Namespace, p: dict[str, Path]) -> int:
    if not p["manifest"].exists():
        print(json.dumps({**planned_actions(p, "uninstall"), "installed": False}, ensure_ascii=False, indent=2))
        return 0
    manifest = json.loads(p["manifest"].read_text(encoding="utf-8"))
    if args.dry_run:
        print(json.dumps({**planned_actions(p, "uninstall"), "dry_run": True, "backup_root": manifest.get("backup_root")}, ensure_ascii=False, indent=2))
        return 0

    managed_keys = ["skill_target", "config"]
    if manifest.get("legacy_migrated"):
        managed_keys.append("legacy_policy")
    conflicts = [
        key
        for key in managed_keys
        if hash_path(p[key]) != manifest.get("managed", {}).get(key)
    ]
    agents_content = p["global_agents"].read_text(encoding="utf-8", errors="strict") if p["global_agents"].exists() else ""
    if START_MARKER not in agents_content or END_MARKER not in agents_content:
        conflicts.append("global_agents_marker")
    if conflicts and not args.force:
        print(json.dumps({"uninstalled": False, "conflicts": conflicts, "backup_root": manifest.get("backup_root")}, ensure_ascii=False, indent=2))
        return 1

    restore_conflicts: list[str] = []
    restore_original("skill_target", p, manifest, restore_conflicts)
    restore_original("config", p, manifest, restore_conflicts)
    if manifest.get("legacy_migrated"):
        restore_original("legacy_policy", p, manifest, restore_conflicts)

    if p["global_agents"].exists():
        updated, found = remove_agents_block(agents_content)
        if not found:
            if args.force:
                updated = agents_content
            else:
                raise RuntimeError("LeanSkill AGENTS marker disappeared during uninstall")
        elif updated:
            atomic_write(p["global_agents"], updated.encode("utf-8"))
        else:
            original = manifest["originals"]["global_agents"]
            if original["existed"]:
                backup_item(Path(original["backup"]), p["global_agents"])
            else:
                p["global_agents"].unlink()

    if conflicts and args.force:
        for key in conflicts:
            if key in {"skill_target", "config", "legacy_policy"}:
                original = manifest["originals"][key]
                target = p[key]
                if target.exists():
                    shutil.rmtree(target) if target.is_dir() else target.unlink()
                if original["existed"]:
                    backup_item(Path(original["backup"]), target)

    p["manifest"].unlink()
    print(json.dumps({"uninstalled": True, "conflicts": conflicts, "backup_root": manifest.get("backup_root")}, ensure_ascii=False, indent=2))
    return 0


def status(p: dict[str, Path]) -> int:
    manifest = json.loads(p["manifest"].read_text(encoding="utf-8")) if p["manifest"].exists() else {}
    agents_text = p["global_agents"].read_text(encoding="utf-8", errors="replace") if p["global_agents"].exists() else ""
    checks = {
        "manifest": p["manifest"].is_file(),
        "skill": (p["skill_target"] / "SKILL.md").is_file(),
        "agents_marker": START_MARKER in agents_text and END_MARKER in agents_text,
        "config": p["config"].is_file(),
    }
    if manifest:
        checks["skill_unmodified"] = hash_path(p["skill_target"]) == manifest.get("managed", {}).get("skill_target")
        checks["config_unmodified"] = hash_path(p["config"]) == manifest.get("managed", {}).get("config")
    valid = all(checks.values())
    print(json.dumps({"installed": valid, "version": manifest.get("version"), "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if valid else 1


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("command", choices=("install", "status", "uninstall"))
    result.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    default_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    result.add_argument("--codex-home", type=Path, default=default_home)
    result.add_argument("--global-agents", type=Path)
    result.add_argument("--shared-skills", type=Path, default=Path.home() / ".agents" / "skills")
    result.add_argument("--skip-plugins", action="store_true")
    result.add_argument("--dry-run", action="store_true")
    result.add_argument("--force", action="store_true")
    result.add_argument("--record-outcomes", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    p = paths(args)
    p["skip_plugins"] = args.skip_plugins
    try:
        if args.command == "install":
            return install(args, p)
        if args.command == "uninstall":
            return uninstall(args, p)
        return status(p)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
