#!/usr/bin/env python3
"""Fail closed on common open-source packaging and privacy mistakes."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "LICENSE",
    "NOTICE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "skills/leanskill-router/SKILL.md",
    "skills/leanskill-router/agents/openai.yaml",
    "scripts/install.py",
    "scripts/policy_manager.py",
    "catalog/schema.json",
    "catalog/registry.example.json",
    "catalog/candidates.example.json",
    "catalog/verified.example.json",
    "catalog/rejected.example.json",
    "catalog/gaps.example.json",
    "evals/catalog.fixture.json",
    ".github/workflows/ci.yml",
]
SKIP_PARTS = {".git", "__pycache__", "quarantine", "reports"}
SKIP_FILES = {
    ROOT / "catalog" / "registry.json",
    ROOT / "catalog" / "candidates.json",
    ROOT / "catalog" / "verified.json",
    ROOT / "catalog" / "rejected.json",
    ROOT / "catalog" / "gaps.json",
}
TEXT_SUFFIXES = {"", ".md", ".py", ".json", ".yaml", ".yml", ".txt"}
PATTERNS = {
    "absolute_user_path": re.compile(r"/(?:Users|home)/[^/\s]+/"),
    "private_key": re.compile(r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
    "github_token": re.compile(r"gh[opsu]_[A-Za-z0-9]{20,}"),
    "todo_placeholder": re.compile(r"\[" + "TODO:" + "|" + "TODO_" + "PLACEHOLDER"),
}


def tracked_files() -> list[Path] | None:
    process = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=False)
    if process.returncode:
        return None
    return [ROOT / item.decode("utf-8") for item in process.stdout.split(b"\0") if item]


def public_files() -> list[Path]:
    tracked = tracked_files()
    if tracked is not None:
        return tracked
    result = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path in SKIP_FILES or any(part in SKIP_PARTS for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix == ".pyc":
            continue
        result.append(path)
    return sorted(result)


def main() -> int:
    errors = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    skill = ROOT / "skills" / "leanskill-router" / "SKILL.md"
    if skill.is_file():
        text = skill.read_text(encoding="utf-8", errors="replace")
        if not text.startswith("---\n") or "name: leanskill-router" not in text.split("---", 2)[1]:
            errors.append("invalid LeanSkill router frontmatter")
    metadata = ROOT / "skills" / "leanskill-router" / "agents" / "openai.yaml"
    if metadata.is_file() and "$leanskill-router" not in metadata.read_text(encoding="utf-8", errors="replace"):
        errors.append("openai.yaml default prompt does not reference $leanskill-router")

    try:
        json.loads((ROOT / "catalog" / "schema.json").read_text(encoding="utf-8"))
        json.loads((ROOT / "evals" / "catalog.fixture.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"invalid JSON: {error}")

    files = public_files()
    for path in files:
        relative = path.relative_to(ROOT)
        if path == ROOT / "catalog" / "registry.json":
            errors.append("generated catalog is tracked")
            continue
        if path.suffix not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{label}: {relative}")

    result = {"valid": not errors, "files_checked": len(files), "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
