"""The PSO audit reports counts and rates without exposing keys."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('pso_preheat_audit', REPO / 'scripts/pso_preheat_audit.py')
assert spec and spec.loader
audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)


class PreheatAudit(unittest.TestCase):
    def test_overlap_and_log_counters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); seed = root / 'seed.tsv'; user = root / 'user.tsv'; log = root / 'log.txt'
            seed.write_text('# seed\nS\taaaa\t0\nR\tbeef\nR\tbeef\n')
            user.write_text('S\taaaa\t0\nC\tcccc\nR\tface\n')
            log.write_text('on the submit thread pipelines 12.5 ms; all threads: archive lookups found 2 / 1 ms, found none 3 / 2 ms\n'
                           'pipeline wait 25.0 ms (demand)\n')
            result = audit.audit(seed, user, log)
            self.assertEqual((result['seed_duplicates'], result['user_already_seeded'], result['user_new'], result['prewarm_unique']), (1, 1, 2, 4))
            self.assertEqual(result['runtime']['archive_hit_rate'], 0.4)
            self.assertEqual(result['runtime']['submit_pso_ms'], 12.5)
            self.assertNotIn('aaaa', str(result))

    def test_invalid_row_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.tsv'; path.write_text('S\tmissing-stage\n')
            with self.assertRaisesRegex(ValueError, 'invalid PSO manifest row'):
                audit.rows(path)


if __name__ == '__main__': unittest.main()
