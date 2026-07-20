#!/usr/bin/env python3
"""Validate the catalog contract without third-party dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


VALID_STATUSES = {"preferred", "available-explicit", "available-implicit", "candidate", "quarantined", "verified", "rejected", "cached-not-enabled", "missing"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", type=Path)
    args = parser.parse_args()
    data = json.loads(args.catalog.read_text(encoding="utf-8"))
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    if not isinstance(data.get("generated_at"), str):
        errors.append("generated_at must be a string")
    skills = data.get("skills")
    plugins = data.get("plugins")
    if not isinstance(skills, list):
        errors.append("skills must be an array")
        skills = []
    if not isinstance(plugins, list):
        errors.append("plugins must be an array")
        plugins = []
    ids: set[str] = set()
    required = {"id", "name", "invocation", "path", "origin", "status", "implicit_invocation", "capabilities", "trust_tier"}
    for index, item in enumerate(skills):
        missing = sorted(required - set(item)) if isinstance(item, dict) else sorted(required)
        if missing:
            errors.append(f"skills[{index}] missing {missing}")
            continue
        if item["id"] in ids:
            errors.append(f"duplicate skill id: {item['id']}")
        ids.add(item["id"])
        if item["status"] not in VALID_STATUSES:
            errors.append(f"invalid status: {item['status']}")
        if not isinstance(item["implicit_invocation"], bool):
            errors.append(f"implicit_invocation is not boolean: {item['id']}")
        if not isinstance(item["capabilities"], list):
            errors.append(f"capabilities is not an array: {item['id']}")
        value_profile = item.get("value_profile")
        if value_profile is not None:
            if not isinstance(value_profile, dict):
                errors.append(f"value_profile is not an object: {item['id']}")
            else:
                allowed = {"context_cost", "native_overlap", "maintenance"}
                if set(value_profile) - allowed:
                    errors.append(f"value_profile has unknown fields: {item['id']}")
                if value_profile.get("context_cost", "unknown") not in {"low", "medium", "high", "unknown"}:
                    errors.append(f"invalid context_cost: {item['id']}")
                if value_profile.get("native_overlap", "unknown") not in {"low", "medium", "high", "unknown"}:
                    errors.append(f"invalid native_overlap: {item['id']}")
                if value_profile.get("maintenance", "unknown") not in {"current", "stale", "unknown"}:
                    errors.append(f"invalid maintenance: {item['id']}")
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({
        "valid": True,
        "skills": len(skills),
        "plugins": len(plugins),
        "implicit": sum(1 for item in skills if item["implicit_invocation"]),
        "explicit": sum(1 for item in skills if not item["implicit_invocation"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
