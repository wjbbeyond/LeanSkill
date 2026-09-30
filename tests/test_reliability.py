import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    spec = importlib.util.spec_from_file_location(Path(relative).stem, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReliabilityTests(unittest.TestCase):
    def test_names_do_not_grant_trust(self):
        catalog = load('scripts/build_catalog.py')
        with tempfile.TemporaryDirectory() as folder:
            skill = Path(folder) / 'SKILL.md'
            for name in ['leanskill-router', 'design-taste-frontend']:
                skill.write_text(f'---\nname: {name}\n---\n')
                self.assertEqual(catalog.make_entry(skill, 'personal')['trust_tier'], 'local-unverified')
                self.assertNotEqual(catalog.make_entry(skill, 'plugin-unverified')['trust_tier'], 'official-plugin')

    def test_custom_home(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            (home / 'leanskill').mkdir()
            (home / 'leanskill/config.json').write_text(json.dumps({'lab_root': folder, 'record_outcomes': True}))
            with patch.dict('os.environ', {'CODEX_HOME': folder}):
                for name, function in [('route', 'default_config'), ('record_outcome', 'load_config')]:
                    module = load(f'skills/leanskill-router/scripts/{name}.py')
                    self.assertEqual(getattr(module, function)()['lab_root'], folder)

    def test_failed_second_write_rolls_back_and_keeps_manifest(self):
        policy = load('scripts/policy_manager.py')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            targets = []
            for name in ['one', 'two']:
                skill = root / name
                (skill / 'agents').mkdir(parents=True)
                (skill / 'agents/openai.yaml').write_text('policy:\n  allow_implicit_invocation: true\n')
                targets.append(('test', root, skill))
            write = policy.atomic_write
            def fail_second(path, data):
                if path == root / 'two/agents/openai.yaml':
                    raise OSError('simulated disk failure')
                write(path, data)
            backup = root / 'backup'
            with patch.object(policy, 'atomic_write', side_effect=fail_second):
                with self.assertRaises(OSError):
                    policy.apply_changes(targets, backup)
            self.assertTrue((backup / 'manifest.json').is_file())
            self.assertIn('true', (root / 'one/agents/openai.yaml').read_text())
            self.assertEqual(policy.restore(backup / 'manifest.json')['conflicts'], 0)
