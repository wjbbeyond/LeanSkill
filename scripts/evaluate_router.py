#!/usr/bin/env python3
"""Run synthetic routing checks against the deterministic router."""

from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
from pathlib import Path


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("leanskill_router", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import router: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--router", type=Path, required=True)
    parser.add_argument("--cases", type=Path, default=Path(__file__).resolve().parents[1] / "evals" / "router_cases.json")
    args = parser.parse_args()
    router = load_module(args.router.resolve())
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    cases = json.loads(args.cases.read_text(encoding="utf-8"))["cases"]
    failures = []
    results = []
    with tempfile.TemporaryDirectory(prefix="leanskill-eval-") as temp_root:
        base = Path(temp_root)
        for case in cases:
            project = base / case["name"]
            project.mkdir()
            for relative, content in case["markers"].items():
                path = project / relative
                if relative.endswith((".xcodeproj", ".xcworkspace")):
                    path.mkdir(parents=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content, encoding="utf-8")
            result = router.build_route(project, case["task"], catalog, None, None, None)
            checks = {
                "project_type": result["profile"]["project_type"] == case["expected_type"],
                "phase": "expected_phase" not in case or result["profile"]["phase"] == case["expected_phase"],
                "quality": "expected_quality" not in case or result["profile"]["quality"] == case["expected_quality"],
                "risk": "expected_risk" not in case or result["profile"]["risk"] == case["expected_risk"],
                "primary": "expected_primary" not in case or result["primary"] == case["expected_primary"],
                "specialists": all(item in result["specialists"] for item in case.get("expected_specialists", [])),
                "gap": "expected_gap" not in case or any(gap.get("candidate_plugin") == case["expected_gap"] for gap in result["gaps"]),
                "max_three": result["selected_count"] <= 3,
                "no_auto_install": result["rules"]["auto_install"] is False,
                "plan_once": result["rules"]["routing_mode"] == "plan-once",
                "no_automatic_reroute": result["rules"]["automatic_reroute"] is False,
                "native_execution": result["rules"]["post_plan_owner"] == "native-codex",
                "receipt_before_scan": result["rules"]["receipt_before_deep_inspection"] is True,
                "bounded_first_pass": result["rules"]["pre_route_command_batches"] <= 5,
            }
            if not all(checks.values()):
                failures.append({"case": case["name"], "checks": checks, "result": result})
            results.append({"case": case["name"], "passed": all(checks.values()), "selected_count": result["selected_count"]})
    summary = {"passed": len(cases) - len(failures), "total": len(cases), "failures": failures, "results": results}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
