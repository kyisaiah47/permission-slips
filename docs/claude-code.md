[← Back to README](../README.md)

# Claude Code setup

Claude Code runs the plugin's two hooks. Nothing is guarded until you write a config.

## Plugin

Install the plugin from a Claude Code session:

```text
/plugin marketplace add kyisaiah47/permission-slips
/plugin install permission-slips@permission-slips
```

The plugin registers `slip.py issue` as a `UserPromptSubmit` hook and `slip.py check` as a `PreToolUse` hook on every tool. It also adds the `slip` skill that explains slips to the agent.

## By hand

You can also install it by hand. Copy the script to a stable path and add the hooks from `examples/claude-code/settings.json`:

```sh
git clone https://github.com/kyisaiah47/permission-slips.git
mkdir -p ~/.permission-slips
cp permission-slips/slips/slip.py ~/.permission-slips/slip.py
```

```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "command": "python3 ~/.permission-slips/slip.py issue", "timeout": 10 } ] }
    ],
    "PreToolUse": [
      { "matcher": "*", "hooks": [ { "type": "command", "command": "python3 ~/.permission-slips/slip.py check", "timeout": 10 } ] }
    ]
  }
}
```

## Config

Write the config. The guard looks for it in this order:

1. `PERMISSION_SLIPS_CONFIG`
2. `.permission-slips.json` in the session's working directory
3. `~/.config/permission-slips/config.json`

```sh
mkdir -p ~/.config/permission-slips
cp permission-slips/slips/config.example.json ~/.config/permission-slips/config.json
```

## Spending from your scripts

Your scripts call `spend` to end until-spent slips. The plugin's own copy lives in the plugin cache, so keep a copy at `~/.permission-slips/slip.py` for scripts to call. Any copy works because the ledger location does not depend on where the script lives.

```sh
python3 ~/.permission-slips/slip.py spend deploy api
```

## Checking it

Check the installation in a new session. Ask for a guarded action without a slip and watch the hook deny it. Type the slip and try again. `PERMISSION_SLIPS_SESSION=<id> python3 ~/.permission-slips/slip.py list` prints what the session holds.

The tests run both hooks end to end with no dependencies:

```sh
python3 -m unittest discover -s tests
```

---

[← Prev](threat-model.md) (Threat model) | [Next →](codex.md) (Codex setup)
