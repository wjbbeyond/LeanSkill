from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "skills" / "leanskill-router" / "scripts" / "route.py"
CATALOG = json.loads((ROOT / "evals" / "catalog.fixture.json").read_text(encoding="utf-8"))
OUTCOME = json.loads((ROOT / "evals" / "outcome.fixture.json").read_text(encoding="utf-8"))


def load_router():
    spec = importlib.util.spec_from_file_location("leanskill_router_value_test", ROUTER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load router")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RouterValueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = load_router()
        self.temporary = tempfile.TemporaryDirectory(prefix="leanskill-router-value-")
        self.project = Path(self.temporary.name)
        (self.project / "package.json").write_text(
            '{"dependencies":{"next":"latest","react":"latest"}}',
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_negated_release_constraints_do_not_change_intent(self) -> None:
        task = "在不安装插件、不部署发布的前提下继续实现并验证未完成部分"
        result = self.router.build_route(self.project, task, CATALOG, None, None, None)
        self.assertEqual(result["profile"]["phase"], "implementation")
        self.assertEqual(result["profile"]["risk"], "low")
        self.assertGreaterEqual(len(result["classification"]["ignored_negated_constraints"]), 2)
        self.assertTrue(result["rules"]["receipt_before_deep_inspection"])
        self.assertLessEqual(result["rules"]["pre_route_command_batches"], 5)
        self.assertEqual(result["rules"]["routing_mode"], "plan-once")
        self.assertFalse(result["rules"]["automatic_reroute"])
        self.assertEqual(result["rules"]["post_plan_owner"], "native-codex")

    def test_matching_outcome_increases_evidence_not_claimed_efficiency(self) -> None:
        task = "测试、验证并修复本地页面闭环"
        without_feedback = self.router.build_route(self.project, task, CATALOG, None, None, None)
        with_feedback = self.router.build_route(self.project, task, CATALOG, None, None, None, [OUTCOME])
        before = next(item for item in without_feedback["selection"] if item["role"] == "primary")
        after = next(item for item in with_feedback["selection"] if item["role"] == "primary")
        self.assertGreater(after["decision_score"], before["decision_score"])
        self.assertEqual(after["confidence"], "medium")
        self.assertEqual(after["matching_outcomes"], 1)
        self.assertEqual(after["native_comparison"], "unknown")
        self.assertEqual(with_feedback["value_evidence"]["matching_route_outcomes"], 1)

    def test_repeated_failure_and_worse_tokens_defers_to_native(self) -> None:
        task = "测试、验证并修复本地页面闭环"
        bad_records = []
        for invocation in ("build-web-apps:frontend-testing-debugging", "browser:control-in-app-browser"):
            for _ in range(3):
                bad_records.append({
                    "schema_version": 1,
                    "profile": {"project_type": "web", "phase": "test", "quality": "production", "risk": "low"},
                    "route": {"primary": invocation, "specialists": []},
                    "outcome": {"status": "failure", "gates": {}, "external_blockers": [], "token_efficiency": "worse"},
                })
        result = self.router.build_route(self.project, task, CATALOG, None, None, None, bad_records)
        self.assertIsNone(result["primary"])
        self.assertEqual(result["gaps"][0]["action"], "use-native-codex-observed-negative-value")
        self.assertTrue(all(item["negative_optimization"] for item in result["alternatives"]))

    def test_plan_is_advisory_path_safe_and_not_overwritten(self) -> None:
        result = self.router.build_route(
            self.project,
            "规划一个新的高端 React 产品",
            CATALOG,
            None,
            None,
            None,
        )
        target = self.router.write_plan(
            self.project,
            self.router.DEFAULT_PLAN_PATH,
            result,
        )
        text = target.read_text(encoding="utf-8")
        self.assertEqual(target, (self.project / "docs" / "LEANSKILL_PLAN.md").resolve())
        self.assertIn("Plan Once, Execute Native", text)
        self.assertIn("Native Codex owns implementation", text)
        self.assertIn("not a permanent Skill whitelist", text)
        self.assertNotIn(str(self.project), text)
        with self.assertRaisesRegex(ValueError, "plan already exists"):
            self.router.write_plan(self.project, self.router.DEFAULT_PLAN_PATH, result)

    def test_plan_refuses_path_outside_project(self) -> None:
        result = self.router.build_route(self.project, "规划新项目", CATALOG, None, None, None)
        with self.assertRaisesRegex(ValueError, "inside the project root"):
            self.router.write_plan(self.project, Path("../outside.md"), result)


if __name__ == "__main__":
    unittest.main()
