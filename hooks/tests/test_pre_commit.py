"""Runs hooks/pre-commit on a scratch git repo for each case."""
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "pre-commit"
LONG = "Zq8vK2mT9xLp4WnR7sYb3HcD"  # 24 characters, fake


def stage_and_run(filename, content):
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        path = repo / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        subprocess.run(["git", "add", "-f", filename], cwd=repo, check=True)
        result = subprocess.run(["sh", str(HOOK)], cwd=repo, capture_output=True, text=True)
        return result


class SecretGuardTests(unittest.TestCase):
    def blocked(self, content, filename="config.txt"):
        r = stage_and_run(filename, content + "\n")
        self.assertEqual(r.returncode, 1, f"expected block for {content!r}: {r.stderr}")
        self.assertNotIn(LONG, r.stderr + r.stdout, "value must never be printed")

    def allowed(self, content, filename="config.txt"):
        r = stage_and_run(filename, content + "\n")
        self.assertEqual(r.returncode, 0, f"expected pass for {content!r}: {r.stderr}")

    # Positive cases
    def test_lowercase_quoted(self):
        self.blocked(f'api_key = "{LONG}"')

    def test_uppercase_quoted(self):
        self.blocked(f'API_KEY="{LONG}"')

    def test_unquoted(self):
        self.blocked(f"API_KEY={LONG}")

    def test_export_unquoted(self):
        self.blocked(f"export SECRET={LONG}")

    def test_export_quoted_single(self):
        self.blocked(f"export DB_PASSWORD='{LONG}'")

    def test_suffix_name(self):
        self.blocked(f"GITHUB_TOKEN={LONG}")

    def test_json_style(self):
        self.blocked(f'{{"password": "{LONG}"}}')

    def test_yaml_style(self):
        self.blocked(f"token: {LONG}")

    def test_known_prefixes(self):
        self.blocked("key = sk-" + "a1B2c3D4e5F6g7H8i9J0k1")
        self.blocked("AKIA" + "ABCDEFGHIJKLMNOP")

    def test_private_key_block(self):
        self.blocked("-----BEGIN RSA PRIVATE KEY-----")

    def test_blocked_filename(self):
        self.blocked("hello", filename=".env")

    # Negative cases
    def test_placeholder_short(self):
        self.allowed("API_KEY=your-key-here")

    def test_empty_value(self):
        self.allowed("API_KEY=")
        self.allowed('API_KEY=""')

    def test_long_placeholder(self):
        self.allowed("API_KEY=your-api-key-goes-here-please")

    def test_env_reference(self):
        self.allowed("API_KEY=${API_KEY_FROM_ENV_FILE_SOMEWHERE}")
        self.allowed('api_key = os.environ["API_KEY"]')

    def test_code_call_not_a_value(self):
        self.allowed("const token = getTokenFromHeaderXyzabcdefgh(req)")

    def test_prose(self):
        self.allowed("Keep every secret out of the repository history.")

    def test_example_file_name_allowed(self):
        self.allowed("API_KEY=", filename=".env.example")


if __name__ == "__main__":
    unittest.main()
