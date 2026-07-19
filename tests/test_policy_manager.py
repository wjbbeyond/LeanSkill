from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "scripts" / "policy_manager.py"


class PolicyManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="leanskill-policy-test-")
        self.base = Path(self.temporary.name)
        self.codex = self.base / "codex-skills"
        self.shared = self.base / "shared-skills"
        self.backup = self.base / "backup"
        (self.codex / "alpha" / "agents").mkdir(parents=True)
        (self.codex / "alpha" / "SKILL.md").write_text("---\nname: alpha\ndescription: alpha skill\n---\n", encoding="utf-8")
        (self.codex / "alpha" / "agents" / "openai.yaml").write_text("policy:\n  allow_implicit_invocation: true\n", encoding="utf-8")
        (self.shared / "beta").mkdir(parents=True)
        (self.shared / "beta" / "SKILL.md").write_text("---\nname: beta\ndescription: beta skill\n---\n", encoding="utf-8")
        (self.codex / "leanskill-router").mkdir()
        (self.codex / "leanskill-router" / "SKILL.md").write_text("---\nname: leanskill-router\ndescription: router\n---\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_policy(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(POLICY), "--codex-skills", str(self.codex), "--shared-skills", str(self.shared), *extra],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_apply_and_restore(self) -> None:
        dry = self.run_policy("--dry-run")
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertEqual(json.loads(dry.stdout)["targets"], 2)

        applied = self.run_policy("--apply", "--backup-root", str(self.backup))
        self.assertEqual(applied.returncode, 0, applied.stderr)
        manifest = Path(json.loads(applied.stdout)["manifest_path"])
        self.assertIn("allow_implicit_invocation: false", (self.codex / "alpha" / "agents" / "openai.yaml").read_text(encoding="utf-8"))
        self.assertIn("allow_implicit_invocation: false", (self.shared / "beta" / "agents" / "openai.yaml").read_text(encoding="utf-8"))
        self.assertFalse((self.codex / "leanskill-router" / "agents" / "openai.yaml").exists())

        restored = self.run_policy("--restore", str(manifest))
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertIn("allow_implicit_invocation: true", (self.codex / "alpha" / "agents" / "openai.yaml").read_text(encoding="utf-8"))
        self.assertFalse((self.shared / "beta" / "agents" / "openai.yaml").exists())


if __name__ == "__main__":
    unittest.main()
