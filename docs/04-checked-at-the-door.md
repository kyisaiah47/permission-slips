[← Back to README](../README.md)

# 4. Checked at the door

*The guard runs outside the model and fails closed.*

One prompt asking for a new page across seven repos started seven agents in parallel. The resulting cap is a hook that the host runs before each tool call. The model cannot argue with the hook, skip it or decide that it does not apply. The first version had a race because parallel calls in one turn could not see each other. The cap moved to a locked per-session state file that fails closed.

## The rule

The `PreToolUse` hook sees every tool call before it runs. It denies a guarded call that has no valid slip and gives the agent a reason. A call with no matching rule passes untouched.

```json
"PreToolUse": [
  { "matcher": "*", "hooks": [ { "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/slips/slip.py\" check", "timeout": 10 } ] }
]
```

The agent sees the reason and the exact command to ask you for:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
  "permissionDecisionReason": "production deploy needs a permission slip. Only the user can issue one, by typing: /slip deploy api"}}
```

## Fails closed

If the config exists but cannot be read or is invalid, every tool call is denied until you fix it. A broken policy guards everything rather than nothing. If no config exists, the hooks stay out of the way. Installing the plugin changes nothing until you write a policy.

```python
    if not config_path(event.get("cwd")).exists():
        return 0  # not set up here: the hook stays out of the way
    try:
        cfg, cfg_path = load_config(event.get("cwd"))
    except Exception as e:  # fail closed: a broken policy guards everything until it's fixed
        return deny(f"permission-slips config could not be read ({e}). Fix the config first.")
    reason = protects_itself(tool, tool_input, cfg_path)
    if reason:
        return deny(reason)
```

The guard protects its own inputs. It denies a write or shell call that names the ledger directory or a config file, regardless of the slips held.

## One script, two hosts

Claude Code and Codex send the same hook JSON on stdin and read the same deny response. One script serves both hosts. Rules can name either host's tool names: `Bash` in Claude Code and `exec_command` in Codex.

---

[← Prev](03-good-for-one-trip.md) (3. Good for one trip) | [Next →](05-how-i-use-them.md) (How I use them)
