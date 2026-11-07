import hashlib
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_release", ROOT / "scripts" / "build_release.py")
build_release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_release)


class BuildReleaseTests(unittest.TestCase):
    def build(self, out):
        return build_release.build(ROOT, Path(out))

    def test_zip_is_deterministic_and_checksummed(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            za, sa = self.build(a)
            zb, sb = self.build(b)
            self.assertEqual(za.read_bytes(), zb.read_bytes())
            digest = hashlib.sha256(za.read_bytes()).hexdigest()
            line = sa.read_text(encoding="utf-8").strip()
            self.assertEqual(f"{digest}  {za.name}", line)
            self.assertEqual(sa.read_text(encoding="utf-8"), sb.read_text(encoding="utf-8"))

    def test_contents_are_skill_folder_plus_license_notices_and_nothing_else(self):
        with tempfile.TemporaryDirectory() as out:
            z, _ = self.build(out)
            names = sorted(zipfile.ZipFile(z).namelist())
            self.assertEqual(
                ["LICENSE", "THIRD_PARTY_NOTICES.md",
                 "agent-handoff-manager/SKILL.md", "agent-handoff-manager/scripts/handoff.py"], names)

    def test_name_carries_core_version_and_core_runs_from_extracted_copy(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as out:
            z, _ = self.build(out)
            self.assertIn("0.2.0-pilot", z.name)
            dest = Path(out) / "x"
            zipfile.ZipFile(z).extractall(dest)
            r = subprocess.run([sys.executable, "-I", str(dest / "agent-handoff-manager" / "scripts" / "handoff.py"), "--version"],
                               capture_output=True, text=True)
            self.assertEqual(0, r.returncode, r.stderr)
            self.assertIn("0.2.0-pilot", r.stdout)

    def test_refuses_dirty_or_unreadable_inputs(self):
        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaises(FileNotFoundError):
                build_release.build(Path(empty), Path(empty) / "out")


if __name__ == "__main__":
    unittest.main()
