"""Acceptance #7: secret/token fixtures must not reach a handoff. Fixtures are fake and assembled at runtime."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "agent-handoff-manager" / "scripts"))
import handoff

A = "A1b2C3d4E5f6G7h8I9j0"
FAKE = {
    "github classic": "gh" + "p_" + A + "K1L2",
    "github fine-grained": "github_" + "pat_" + A + "K1L2M3",
    "openai style": "sk-" + A + A,
    "aws access key": "AK" + "IA" + "ABCDEFGHIJKLMNOP",
    "slack": "xo" + "xb-" + "1234567890-" + A,
    "google api": "AI" + "za" + "Sy" + A + "K1L2M3N4O5P6",
    "stripe live": "sk_" + "live_" + A + "K1",
    "gitlab": "gl" + "pat-" + A + "K1",
    "npm": "npm" + "_" + A + "K1L2M3N4O5P6Q7R8S9T0U1V2W3X4",
    "jwt": "ey" + "JhbGciOiJIUzI1NiJ9." + "ey" + "JzdWIiOiIxMjM0NTY3ODkwIn0." + "abcDEF123-_xyz",
    "private key": "-----BEGIN " + "OPENSSH PRIVATE KEY-----",
    "url credentials": "postgres://admin:" + "hunter2hunter2@db.internal:5432/app",
    "env assignment": "DB_PASSWORD=" + "correcthorsebattery",
    "bearer": "Authorization: Bearer " + A + A,
    "azure storage": "AccountKey=" + A + A + "==",
    "sendgrid": "SG" + "." + A + "." + A + "abc",
}
SAFE = [
    "Discuss the password reset flow and token budget for the API client",
    "Run pytest -q; 0 failed",
    "commit 0123456789abcdef0123456789abcdef01234567 on branch feature/auth",
    "see https://example.com/docs/api-keys for how keys are rotated",
    "Use environment variable API_KEY from the vault (do not paste it)",
    "skills are listed in .agents/skills/agent-handoff-manager",
]


class SecretScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def payload(self, text, field="next_action"):
        p = {"mission": "m", "next_action": "n"}
        if field in ("failed_attempts", "decisions", "completed"):
            p[field] = [text]
        elif field == "evidence":
            p["validation"] = [{"command": "x", "result": "failed", "evidence": text}]
        else:
            p[field] = text
        return p

    def test_every_fake_secret_is_rejected_in_every_text_location(self):
        for name, secret in FAKE.items():
            for field in ("mission", "next_action", "failed_attempts", "decisions", "completed", "evidence"):
                with self.subTest(secret=name, field=field):
                    with self.assertRaisesRegex(handoff.HandoffError, "credential"):
                        handoff.write(self.root, self.payload(f"context {secret} end", field))
        self.assertEqual([], handoff.list_records(self.root))

    def test_ordinary_text_is_not_rejected(self):
        for text in SAFE:
            with self.subTest(text=text):
                handoff.write(self.root, self.payload(text))

    def test_rejection_message_never_echoes_the_secret(self):
        for secret in FAKE.values():
            try:
                handoff.write(self.root, self.payload(secret))
            except handoff.HandoffError as exc:
                self.assertNotIn(secret, str(exc))


if __name__ == "__main__":
    unittest.main()
