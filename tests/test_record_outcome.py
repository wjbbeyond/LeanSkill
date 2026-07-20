from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORDER = ROOT / "skills" / "leanskill-router" / "scripts" / "record_outcome.py"
FIXTURE = ROOT / "evals" / "outcome.fixture.json"


class RecordOutcomeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="leanskill-outcome-")
        self.base = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_dry_run_and_private_append(self) -> None:
        dry = subprocess.run(
            [sys.executable, str(RECORDER), "--input", str(FIXTURE), "--dry-run"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(dry.returncode, 0, dry.stdout + dry.stderr)
        self.assertFalse(json.loads(dry.stdout)["written"])

        output = self.base / "outcomes.jsonl"
        write = subprocess.run(
            [sys.executable, str(RECORDER), "--input", str(FIXTURE), "--output", str(output)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        record = json.loads(output.read_text(encoding="utf-8"))
        self.assertNotIn("project_name", record)
        self.assertNotIn("project_path", record)
        self.assertEqual(record["outcome"]["token_efficiency"], "unknown")
        self.assertEqual(os.stat(output).st_mode & 0o777, 0o600)

    def test_rejects_free_form_identity_fields(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["project_name"] = "private-project"
        invalid = self.base / "invalid.json"
        invalid.write_text(json.dumps(payload), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(RECORDER), "--input", str(invalid), "--dry-run"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("forbidden fields", result.stderr)


if __name__ == "__main__":
    unittest.main()
