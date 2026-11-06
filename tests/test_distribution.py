import tempfile
import unittest
from pathlib import Path
from scripts.validate_distribution import validate, ROOT

class TestDistributionScaffold(unittest.TestCase):
    def test_starter_package_integrity(self):
        self.assertEqual([], validate(ROOT))

    def test_missing_files_reports_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors=validate(Path(tmp))
            self.assertTrue(any('missing' in x for x in errors))

if __name__ == '__main__':
    unittest.main()
