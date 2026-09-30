#!/usr/bin/env python3
"""Record a schema-limited, anonymous LeanSkill routing outcome."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUSES = {"success", "local-success", "local-success-external-blocked", "partial", "failure", "blocked"}
GATE_RESULTS = {"pass", "fail", "blocked", "not-run"}
TOKEN_EFFICIENCY = {"better", "neutral", "worse", "unknown"}
BLOCKERS = {"database", "payments", "queue", "object-storage", "external-provider", "deployment", "secrets", "production-data"}
TOP_LEVEL = {"schema_version", "profile", "route", "outcome"}
PROFILE_FIELDS = {"project_type", "phase", "quality", "risk"}
ROUTE_FIELDS = {"primary", "specialists"}
OUTCOME_FIELDS = {"status", "gates", "external_blockers", "token_efficiency"}
SENSITIVE = re.compile(r"/(?:Users|home)/|\bsk-[A-Za-z0-9_-]{12,}|BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY", re.IGNORECASE)


def load_config() -> dict[str, Any]:
    for path in (
        Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "leanskill" / "config.json",
        Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skill-lab" / "config.json",
    ):
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}


def reject_unknown(actual: set[str], allowed: set[str], label: str) -> None:
    unknown = sorted(actual - allowed)
    if unknown:
        raise ValueError(f"{label} contains forbidden fields: {', '.join(unknown)}")


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if SENSITIVE.search(value):
        raise ValueError(f"{label} may contain a path or secret")
    return value.strip()


def require_identifier(value: Any, label: str) -> str:
    result = require_text(value, label)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", result):
        raise ValueError(f"{label} must be a capability identifier, not free-form text")
    return result


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    reject_unknown(set(payload), TOP_LEVEL, "payload")
    if payload.get("schema_version") != 1:
        raise ValueError("schema_version must equal 1")

    profile = payload.get("profile")
    route = payload.get("route")
    outcome = payload.get("outcome")
    if not isinstance(profile, dict) or not isinstance(route, dict) or not isinstance(outcome, dict):
        raise ValueError("profile, route, and outcome must be objects")
    reject_unknown(set(profile), PROFILE_FIELDS, "profile")
    reject_unknown(set(route), ROUTE_FIELDS, "route")
    reject_unknown(set(outcome), OUTCOME_FIELDS, "outcome")
    if set(profile) != PROFILE_FIELDS:
        raise ValueError("profile requires project_type, phase, quality, and risk")

    clean_profile = {key: require_identifier(profile[key], f"profile.{key}") for key in sorted(PROFILE_FIELDS)}
    primary = route.get("primary")
    if primary is not None:
        primary = require_identifier(primary, "route.primary")
    specialists = route.get("specialists", [])
    if not isinstance(specialists, list) or len(specialists) > 2:
        raise ValueError("route.specialists must be an array with at most two items")
    clean_specialists = [require_identifier(value, "route.specialists[]") for value in specialists]
    if primary is None and not clean_specialists:
        raise ValueError("route must contain a primary or specialist")

    status = outcome.get("status")
    if status not in STATUSES:
        raise ValueError(f"outcome.status must be one of {sorted(STATUSES)}")
    gates = outcome.get("gates", {})
    if not isinstance(gates, dict):
        raise ValueError("outcome.gates must be an object")
    clean_gates: dict[str, str] = {}
    for name, result in gates.items():
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", name):
            raise ValueError("gate names must use lowercase letters, digits, and hyphens")
        if result not in GATE_RESULTS:
            raise ValueError(f"invalid gate result for {name}")
        clean_gates[name] = result
    blockers = outcome.get("external_blockers", [])
    if not isinstance(blockers, list) or any(value not in BLOCKERS for value in blockers):
        raise ValueError(f"external_blockers must use only {sorted(BLOCKERS)}")
    token_efficiency = outcome.get("token_efficiency", "unknown")
    if token_efficiency not in TOKEN_EFFICIENCY:
        raise ValueError(f"token_efficiency must be one of {sorted(TOKEN_EFFICIENCY)}")

    return {
        "schema_version": 1,
        "profile": clean_profile,
        "route": {"primary": primary, "specialists": clean_specialists},
        "outcome": {
            "status": status,
            "gates": clean_gates,
            "external_blockers": sorted(set(blockers)),
            "token_efficiency": token_efficiency,
        },
    }


def parse_gate(values: list[str]) -> dict[str, str]:
    gates = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"invalid gate: {value}; expected name=result")
        name, result = value.split("=", 1)
        gates[name] = result
    return gates


def payload_from_args(args: argparse.Namespace) -> dict[str, Any]:
    if args.input:
        return json.loads(args.input.read_text(encoding="utf-8"))
    required = {
        "project_type": args.project_type,
        "phase": args.phase,
        "quality": args.quality,
        "risk": args.risk,
        "status": args.status,
    }
    missing = [name.replace("_", "-") for name, value in required.items() if not value]
    if missing:
        raise ValueError(f"missing arguments: {', '.join(missing)}")
    return {
        "schema_version": 1,
        "profile": {
            "project_type": args.project_type,
            "phase": args.phase,
            "quality": args.quality,
            "risk": args.risk,
        },
        "route": {"primary": args.primary, "specialists": args.specialist},
        "outcome": {
            "status": args.status,
            "gates": parse_gate(args.gate),
            "external_blockers": args.blocker,
            "token_efficiency": args.token_efficiency,
        },
    }


def append_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--input", type=Path)
    result.add_argument("--output", type=Path)
    result.add_argument("--project-type")
    result.add_argument("--phase")
    result.add_argument("--quality")
    result.add_argument("--risk")
    result.add_argument("--primary")
    result.add_argument("--specialist", action="append", default=[])
    result.add_argument("--status")
    result.add_argument("--gate", action="append", default=[])
    result.add_argument("--blocker", action="append", default=[])
    result.add_argument("--token-efficiency", default="unknown")
    result.add_argument("--dry-run", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    config = load_config()
    payload = validate_payload(payload_from_args(args))
    record = {
        **payload,
        "event_id": str(uuid.uuid4()),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    if args.dry_run:
        print(json.dumps({"valid": True, "record": record, "written": False}, ensure_ascii=False, indent=2))
        return 0
    if args.output:
        output = args.output.expanduser().resolve()
    else:
        if not config.get("record_outcomes", False):
            raise RuntimeError("anonymous outcome recording is disabled; enable record_outcomes or pass --output")
        value = config.get("feedback_path")
        if not value:
            raise RuntimeError("feedback_path is missing from LeanSkill config")
        output = Path(value).expanduser().resolve()
    append_record(output, record)
    print(json.dumps({"valid": True, "written": True, "event_id": record["event_id"], "output": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"valid": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
