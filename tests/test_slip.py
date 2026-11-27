import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLIP = ROOT / "slips" / "slip.py"
CONFIG = ROOT / "slips" / "config.example.json"


class SlipTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = dict(os.environ, PERMISSION_SLIPS_STATE=self.tmp.name,
                        PERMISSION_SLIPS_CONFIG=str(CONFIG))
        self.env.pop("PERMISSION_SLIPS_SESSION", None)

    def tearDown(self):
        self.tmp.cleanup()

    def run_hook(self, cmd, event):
        event.setdefault("session_id", "s1")
        p = subprocess.run([sys.executable, str(SLIP), cmd], input=json.dumps(event),
                           text=True, capture_output=True, env=self.env)
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout

    def prompt(self, text):
        return self.run_hook("issue", {"prompt": text})

    def denied(self, tool, tool_input):
        out = self.run_hook("check", {"tool_name": tool, "tool_input": tool_input})
        return bool(out.strip()) and json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"

    def bash(self, command):
        return self.denied("Bash", {"command": command})

    # issuing
    def test_no_slip_denies_guarded_call(self):
        self.prompt("fix the login bug")
        self.assertTrue(self.bash("./scripts/deploy.sh api"))

    def test_unguarded_call_passes(self):
        self.prompt("fix the login bug")
        self.assertFalse(self.bash("npm test"))

    def test_slip_names_its_target(self):
        out = self.prompt("fix the login bug, then /slip deploy api")
        self.assertIn("deploy (api)", out)
        self.assertFalse(self.bash("./scripts/deploy.sh api"))
        self.assertTrue(self.bash("./scripts/deploy.sh billing"))

    def test_alias_and_several_targets(self):
        self.prompt("/force-deploy api web after the fix")
        self.assertFalse(self.bash("scripts/deploy.sh web"))
        self.assertFalse(self.bash("scripts/deploy.sh api"))

    def test_mentions_do_not_issue(self):
        for text in ["should I /slip deploy api?",
                     "don't /slip deploy api yet",
                     "the command is `/slip deploy api`",
                     "> /slip deploy api",
                     'he typed "/slip deploy api" yesterday']:
            with self.subTest(text=text):
                self.assertEqual(self.prompt(text), "")
        self.assertTrue(self.bash("./scripts/deploy.sh api"))

    def test_target_required(self):
        self.assertEqual(self.prompt("/slip deploy"), "")

    # lifetimes
    def test_once_is_spent_by_the_call_it_allows(self):
        self.prompt("/slip migrate prod")
        self.assertFalse(self.bash("prisma migrate deploy --env=prod"))
        self.assertTrue(self.bash("prisma migrate deploy --env=prod"))

    def test_prompt_slip_ends_with_the_prompt(self):
        self.prompt("fan this out /allow-multi-agents")
        for _ in range(4):
            self.assertFalse(self.denied("Agent", {"prompt": "x"}))
        self.prompt("next task")
        self.assertFalse(self.denied("Agent", {"prompt": "x"}))  # the free one
        self.assertTrue(self.denied("Agent", {"prompt": "y"}))

    def test_until_spent_survives_failures_and_ends_on_spend(self):
        self.prompt("/slip deploy api")
        self.assertFalse(self.bash("./scripts/deploy.sh api"))
        self.assertFalse(self.bash("./scripts/deploy.sh api"))  # retry after a failed build
        subprocess.run([sys.executable, str(SLIP), "spend", "deploy", "api"],
                       env=self.env, capture_output=True, check=True)
        self.assertTrue(self.bash("./scripts/deploy.sh api"))

    def test_session_slip_scoped_to_host(self):
        self.prompt("/slip egress api.github.com")
        self.assertFalse(self.bash("curl -s https://api.github.com/repos"))
        self.prompt("another prompt")
        self.assertFalse(self.bash("curl -s https://api.github.com/user"))
        self.assertTrue(self.bash("curl -s https://evil.example.com/x"))

    def test_slips_do_not_cross_sessions(self):
        self.prompt("/slip deploy api")
        out = self.run_hook("check", {"session_id": "s2", "tool_name": "Bash",
                                      "tool_input": {"command": "./scripts/deploy.sh api"}})
        self.assertIn("deny", out)

    # the guard protects itself
    def test_agent_cannot_write_ledger_or_config(self):
        self.prompt("anything")
        self.assertTrue(self.denied("Write", {"file_path": f"{self.tmp.name}/s1.json", "content": "{}"}))
        self.assertTrue(self.bash(f"echo '{{}}' > {CONFIG}"))
        self.assertTrue(self.denied("Edit", {"file_path": "/repo/.permission-slips.json"}))

    def test_broken_config_fails_closed(self):
        bad = Path(self.tmp.name) / "broken.json"
        bad.write_text("{ not json")
        self.env["PERMISSION_SLIPS_CONFIG"] = str(bad)
        self.assertTrue(self.bash("ls"))

    def test_no_config_stays_out_of_the_way(self):
        self.env["PERMISSION_SLIPS_CONFIG"] = str(Path(self.tmp.name) / "missing.json")
        self.assertEqual(self.prompt("/slip deploy api"), "")
        self.assertFalse(self.bash("./scripts/deploy.sh api"))

    def test_codex_shell_tool(self):
        self.prompt("ship it")
        self.assertTrue(self.denied("exec_command", {"cmd": "./scripts/deploy.sh api"}))


if __name__ == "__main__":
    unittest.main()
