[← Back to README](../README.md)

# Codex setup

Codex sends the same hook JSON as Claude Code, so the same script works. Its shell tool is `exec_command`, which the example rules already match.

Copy the script, the config, and the skill, then add the hooks:

```sh
git clone https://github.com/kyisaiah47/permission-slips.git
mkdir -p ~/.permission-slips ~/.config/permission-slips ~/.agents/skills
cp permission-slips/slips/slip.py ~/.permission-slips/slip.py
cp permission-slips/slips/config.example.json ~/.config/permission-slips/config.json
test ! -e ~/.agents/skills/slip && cp -R permission-slips/skills/slip ~/.agents/skills/slip
```

Merge `examples/codex/hooks.json` into `~/.codex/hooks.json` and keep any hooks you already have. Codex may ask you to trust the new hooks the first time they run.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "command": "python3 ~/.permission-slips/slip.py issue", "timeout": 10, "statusMessage": "Checking for permission slips..." } ] }
    ],
    "PreToolUse": [
      { "hooks": [ { "type": "command", "command": "python3 ~/.permission-slips/slip.py check", "timeout": 10, "statusMessage": "Checking permission slips..." } ] }
    ]
  }
}
```

The config follows the same lookup order as Claude Code: `PERMISSION_SLIPS_CONFIG`, then `.permission-slips.json` in the project, then `~/.config/permission-slips/config.json`.

Start a new Codex session and type the slip in your prompt, for example `/slip deploy api`. The repo also includes a plugin manifest for Codex plugin directories.

---

[← Prev](claude-code.md) (Claude Code setup)
