"""Synthetic manifest comparison, with no game assets or codesigning."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from subprocess import CompletedProcess

REPO = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('build_manifest', REPO / 'scripts/build_manifest.py')
assert spec and spec.loader
manifest = importlib.util.module_from_spec(spec); spec.loader.exec_module(manifest)


class BuildManifest(unittest.TestCase):
    def test_signature_verification_is_required(self):
        ok = CompletedProcess([], 0, b'', b'')
        ent = CompletedProcess([], 0, b'<plist>rights</plist>', b'')
        with patch.object(manifest.subprocess, 'run', side_effect=[ok, ent]) as run:
            result = manifest.signature('/tmp/app')
            self.assertTrue(result['verified'])
            self.assertEqual(len(result['entitlements_sha256']), 64)
            self.assertEqual(run.call_args_list[0].args[0][:4], ['codesign', '--verify', '--deep', '--strict'])
        failed = CompletedProcess([], 1, b'', b'invalid signature')
        with patch.object(manifest.subprocess, 'run', return_value=failed), self.assertRaisesRegex(ValueError, 'invalid signature'):
            manifest.signature('/tmp/app')

    def test_content_and_relative_names_determine_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / 'first'; b = root / 'second'; a.mkdir(); b.mkdir()
            (a / 'shader.metallib').write_bytes(b'good')
            (b / 'shader.metallib').write_bytes(b'good')
            self.assertEqual(manifest.digest(a), manifest.digest(b))
            (b / 'shader.metallib').write_bytes(b'bad!')
            self.assertNotEqual(manifest.digest(a), manifest.digest(b))
            (b / 'shader.metallib').write_bytes(b'good')
            (b / 'other.metallib').write_bytes(b'')
            self.assertNotEqual(manifest.digest(a), manifest.digest(b))

    def test_create_verify_and_changed_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root / 'tool.lock'; source.write_text('v1')
            output = root / 'artifact.ipa'; output.write_bytes(b'ipa')
            path = root / 'manifest.json'
            args = ['--input', f'chain={source}', '--artifact', str(output)]
            manifest.main(['create', str(path), *args])
            self.assertNotIn(str(root), path.read_text())
            manifest.main(['verify', str(path), *args])
            source.write_text('v2')
            with self.assertRaises(SystemExit) as cm: manifest.main(['verify', str(path), *args])
            self.assertEqual(cm.exception.code, 1)


if __name__ == '__main__': unittest.main()
