import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "cursor_claude_parity.py"
EXAMPLE = ROOT / "examples" / "tiny-repo"


def run(repo, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(repo), *args], capture_output=True, text=True
    )


class ParityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "repo"
        shutil.copytree(EXAMPLE, self.repo)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_generates_everything(self):
        self.assertEqual(run(self.repo).returncode, 0)
        for rel in (
            ".mcp.json", "CLAUDE.md", ".claude/rules/house-style.md",
            ".claude/rules/api-conventions.md", ".claude/agents/reviewer.md",
            ".claude/settings.json", ".gitignore",
        ):
            self.assertTrue((self.repo / rel).is_file(), rel)

    def test_env_syntax_and_envfile(self):
        run(self.repo)
        mcp = json.loads((self.repo / ".mcp.json").read_text())["mcpServers"]
        self.assertEqual(mcp["docs"]["headers"]["Authorization"], "Bearer ${DOCS_TOKEN}")
        self.assertEqual(mcp["docs"]["type"], "http")
        self.assertEqual(mcp["search"]["env"]["SEARCH_API_KEY"], "${SEARCH_API_KEY}")
        self.assertNotIn("envFile", mcp["search"])

    def test_agent_pointer_and_model(self):
        run(self.repo)
        text = (self.repo / ".claude/agents/reviewer.md").read_text()
        self.assertIn("Owned by Cursor", text)
        self.assertNotIn("proactively", text)
        self.assertNotIn("model:", text)  # Cursor slug dropped
        self.assertIn(".cursor/agents/reviewer.md", text)

    def test_hook_flag(self):
        run(self.repo)
        settings = json.loads((self.repo / ".claude/settings.json").read_text())
        cmd = settings["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        self.assertTrue(cmd.endswith("--claude"))

    def test_check_clean_then_drift(self):
        run(self.repo)
        self.assertEqual(run(self.repo, "--check").returncode, 0)
        rule = self.repo / ".cursor/rules/house-style.mdc"
        rule.write_text(rule.read_text() + "\nNew line.\n")
        out = run(self.repo, "--check")
        self.assertEqual(out.returncode, 1)
        self.assertIn("drift", out.stderr)
        run(self.repo)
        self.assertEqual(run(self.repo, "--check").returncode, 0)

    def test_hand_written_file_not_overwritten(self):
        (self.repo / ".claude/agents").mkdir(parents=True)
        mine = self.repo / ".claude/agents/reviewer.md"
        mine.write_text("mine\n")
        self.assertEqual(run(self.repo).returncode, 1)
        self.assertEqual(mine.read_text(), "mine\n")

    def test_hand_written_claude_md_kept(self):
        (self.repo / "CLAUDE.md").write_text("# Mine\n\nKeep this.\n")
        run(self.repo)
        text = (self.repo / "CLAUDE.md").read_text()
        self.assertIn("Keep this.", text)
        self.assertIn("claude-parity:start", text)

    def test_refuses_empty_rules(self):
        for f in (self.repo / ".cursor/rules").glob("*"):
            f.unlink()
        self.assertEqual(run(self.repo).returncode, 3)

    def test_no_em_dashes_in_output(self):
        run(self.repo)
        for f in self.repo.rglob("*"):
            if f.is_file() and ".cursor" not in f.parts:
                self.assertNotIn("\u2014", f.read_text(), str(f))


if __name__ == "__main__":
    unittest.main()
