#!/usr/bin/env python3
"""Set user-installed skills to explicit-only with backup and rollback."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def skill_dirs(roots: list[tuple[str, Path]]) -> list[tuple[str, Path, Path]]:
    result: list[tuple[str, Path, Path]] = []
    for label, root in roots:
        if not root.exists():
            continue
        for skill_file in sorted(root.rglob("SKILL.md")):
            relative = skill_file.relative_to(root)
            if label == "codex" and relative.parts and relative.parts[0].startswith("."):
                continue
            if skill_file.parent.name in {"leanskill-router", "project-dev-router"}:
                continue
            result.append((label, root, skill_file.parent))
    return result


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def explicit_only_yaml(original: str) -> str:
    pattern = re.compile(r"^(\s*allow_implicit_invocation\s*:\s*)(true|false)(\s*)$", re.MULTILINE | re.IGNORECASE)
    if pattern.search(original):
        return pattern.sub(lambda match: match.group(1) + "false" + match.group(3), original, count=1)
    policy = re.search(r"^policy\s*:\s*$", original, re.MULTILINE)
    if policy:
        insertion = policy.end()
        return original[:insertion] + "\n  allow_implicit_invocation: false" + original[insertion:]
    suffix = "" if not original or original.endswith("\n") else "\n"
    return original + suffix + "policy:\n  allow_implicit_invocation: false\n"


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        handle.write(data)
        temp_name = handle.name
    os.replace(temp_name, path)


def apply_changes(targets: list[tuple[str, Path, Path]], backup_root: Path) -> dict[str, Any]:
    records = []
    changed = 0
    already_explicit = 0
    updates = []
    backup_root.mkdir(parents=True, exist_ok=False)
    for label, root, skill_dir in targets:
        policy_file = skill_dir / "agents" / "openai.yaml"
        existed = policy_file.exists()
        original = policy_file.read_bytes() if existed else b""
        original_text = original.decode("utf-8", errors="strict") if existed else ""
        updated = explicit_only_yaml(original_text).encode("utf-8")
        relative = policy_file.relative_to(root)
        backup_path = backup_root / "files" / label / relative
        if existed:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(policy_file, backup_path)
        needs_change = original != updated
        if needs_change:
            updates.append((policy_file, updated))
            changed += 1
        else:
            already_explicit += 1
        records.append({
            "root_label": label,
            "root": str(root),
            "target": str(policy_file),
            "existed": existed,
            "original_sha256": sha256(original),
            "updated_sha256": sha256(updated),
            "backup": str(backup_path) if existed else None,
            "changed": needs_change,
        })
    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": "set-explicit-only",
        "records": records,
        "summary": {"targets": len(records), "changed": changed, "already_explicit": already_explicit},
    }
    manifest_path = backup_root / "manifest.json"
    atomic_write(manifest_path, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    manifest["manifest_path"] = str(manifest_path)
    try:
        for policy_file, updated in updates:
            atomic_write(policy_file, updated)
    except OSError:
        # The complete recovery manifest already exists, even if rollback fails.
        restore(manifest_path)
        raise
    return manifest


def restore(manifest_path: Path) -> dict[str, int]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    restored = 0
    removed = 0
    conflicts = 0
    for record in manifest.get("records", []):
        if not record.get("changed"):
            continue
        target = Path(record["target"])
        current = target.read_bytes() if target.exists() else b""
        if sha256(current) == record["original_sha256"]:
            continue
        if sha256(current) != record["updated_sha256"]:
            conflicts += 1
            continue
        if record["existed"]:
            backup = Path(record["backup"])
            atomic_write(target, backup.read_bytes())
            restored += 1
        elif target.exists():
            target.unlink()
            removed += 1
    return {"restored": restored, "removed_new_files": removed, "conflicts": conflicts}


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--restore", type=Path)
    parser.add_argument("--codex-skills", type=Path, default=Path.home() / ".codex" / "skills")
    parser.add_argument("--shared-skills", type=Path, default=Path.home() / ".agents" / "skills")
    parser.add_argument("--backup-root", type=Path)
    args = parser.parse_args()

    if args.restore:
        summary = restore(args.restore.resolve())
        print(json.dumps(summary, ensure_ascii=False))
        return 1 if summary["conflicts"] else 0

    targets = skill_dirs([("codex", args.codex_skills.resolve()), ("shared", args.shared_skills.resolve())])
    absent = sum(1 for _, _, skill_dir in targets if not (skill_dir / "agents" / "openai.yaml").exists())
    present = len(targets) - absent
    if not args.apply:
        print(json.dumps({
            "mode": "dry-run",
            "targets": len(targets),
            "would_create": absent,
            "would_update_or_keep": present,
            "excluded": [".codex/skills/.system", "leanskill-router", "project-dev-router"],
        }, ensure_ascii=False))
        return 0

    backup_root = args.backup_root
    if backup_root is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = Path.home() / ".codex" / "backups" / f"leanskill-policy-{stamp}"
    manifest = apply_changes(targets, backup_root.resolve())
    print(json.dumps({**manifest["summary"], "manifest_path": manifest["manifest_path"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
