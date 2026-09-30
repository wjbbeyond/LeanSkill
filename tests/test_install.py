from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install.py"


class InstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="leanskill-install-test-")
        self.base = Path(self.temporary.name)
        self.repo = self.base / "repo"
        self.codex = self.base / "codex"
        self.shared = self.base / "shared"
        (self.repo / "scripts").mkdir(parents=True)
        (self.repo / "catalog").mkdir()
        shutil.copytree(ROOT / "skills", self.repo / "skills")
        shutil.copy2(ROOT / "scripts" / "build_catalog.py", self.repo / "scripts" / "build_catalog.py")
        for source in (ROOT / "catalog").glob("*.example.json"):
            shutil.copy2(source, self.repo / "catalog" / source.name)
        self.codex.mkdir()
        self.shared.mkdir()
        (self.codex / "AGENTS.md").write_text("# Existing instructions\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_installer(self, command: str, *extra: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        process = subprocess.run(
            [
                sys.executable,
                str(INSTALLER),
                command,
                "--repo-root",
                str(self.repo),
                "--codex-home",
                str(self.codex),
                "--shared-skills",
                str(self.shared),
                "--skip-plugins",
                *extra,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(process.returncode, expected, process.stdout + process.stderr)
        return process

    def test_install_status_upgrade_and_uninstall(self) -> None:
        self.run_installer("install", "--dry-run")
        self.assertFalse((self.codex / "skills" / "leanskill-router").exists())

        self.run_installer("install")
        self.run_installer("status")
        agents = (self.codex / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("<!-- LEANSKILL:START -->", agents)
        self.assertEqual(agents.count("<!-- LEANSKILL:START -->"), 1)
        config = json.loads((self.codex / "leanskill" / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(Path(config["lab_root"]).resolve(), self.repo.resolve())
        self.assertEqual(Path(config["feedback_path"]).resolve(), (self.repo / "state" / "outcomes.jsonl").resolve())
        self.assertEqual(config["routing_mode"], "plan-once")
        self.assertFalse(config["record_outcomes"])
        self.assertIn("native Codex owns execution", agents)
        self.assertIn("Re-run it only when the user explicitly asks", agents)
        self.assertIn("If `docs/LEANSKILL_PLAN.md` already exists, do not re-run", agents)
        self.assertIn("explicitly invoke an installed explicit-only Skill", agents)
        policy = (self.codex / "skills" / "leanskill-router" / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: false", policy)
        self.assertTrue((self.repo / "catalog" / "registry.json").is_file())

        self.run_installer("install", "--record-outcomes")
        config = json.loads((self.codex / "leanskill" / "config.json").read_text(encoding="utf-8"))
        self.assertTrue(config["record_outcomes"])
        self.run_installer("install")
        config = json.loads((self.codex / "leanskill" / "config.json").read_text(encoding="utf-8"))
        self.assertTrue(config["record_outcomes"])
        agents = (self.codex / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(agents.count("<!-- LEANSKILL:START -->"), 1)

        (self.codex / "AGENTS.md").write_text(agents + "# Later user instruction\n", encoding="utf-8")
        self.run_installer("uninstall", "--dry-run")
        self.run_installer("uninstall")
        restored = (self.codex / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("# Existing instructions", restored)
        self.assertIn("# Later user instruction", restored)
        self.assertNotIn("LEANSKILL", restored)
        self.assertFalse((self.codex / "skills" / "leanskill-router").exists())
        self.assertFalse((self.codex / "leanskill" / "config.json").exists())

    def test_uninstall_refuses_modified_managed_skill(self) -> None:
        self.run_installer("install")
        skill = self.codex / "skills" / "leanskill-router" / "SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + "\nmodified\n", encoding="utf-8")
        self.run_installer("uninstall", expected=1)
        self.assertTrue(skill.exists())
        self.assertIn("LEANSKILL:START", (self.codex / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertTrue((self.codex / "leanskill" / "install-manifest.json").exists())

    def test_migrates_and_restores_legacy_router(self) -> None:
        legacy = self.codex / "skills" / "project-dev-router"
        (legacy / "agents").mkdir(parents=True)
        (legacy / "SKILL.md").write_text(
            "---\nname: project-dev-router\ndescription: legacy\n---\n# Project Dev Router\nCodexSkillLab\n",
            encoding="utf-8",
        )
        (legacy / "agents" / "openai.yaml").write_text(
            "policy:\n  allow_implicit_invocation: true\n",
            encoding="utf-8",
        )
        old_agents = (
            "# Global project capability routing\n\n"
            "Use `$project-dev-router` with the verified CodexSkillLab catalog.\n"
        )
        (self.codex / "AGENTS.md").write_text(old_agents, encoding="utf-8")

        old_agents += "\n# User rules\nPreserve my custom instructions.\n"
        (self.codex / "AGENTS.md").write_text(old_agents, encoding="utf-8")
        self.run_installer("install", expected=1)
        self.assertEqual((self.codex / "AGENTS.md").read_text(encoding="utf-8"), old_agents)
        self.assertFalse((self.codex / "skills" / "leanskill-router").exists())
        self.assertIn(
            "allow_implicit_invocation: true",
            (legacy / "agents" / "openai.yaml").read_text(encoding="utf-8"),
        )

        self.run_installer("uninstall")
        self.assertEqual((self.codex / "AGENTS.md").read_text(encoding="utf-8"), old_agents)
        self.assertIn(
            "allow_implicit_invocation: true",
            (legacy / "agents" / "openai.yaml").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
