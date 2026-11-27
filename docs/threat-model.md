[← Back to README](../README.md)

# Threat model

Permission slips stop an agent from acting past your intent. They can stop the agent from deploying the wrong repo, running a migration nobody asked for, or starting ten subagents. They are not a sandbox. Read this before relying on them for anything stronger.

## What it protects against

Slips stop these failures:

- An agent decides on its own that an action is allowed.
- An agent quotes, replays or writes a slip command itself.
- A slip outlives the work it was issued for.
- An agent uses a slip on a target it does not name.
- Parallel calls race to spend the same slip.
- A broken policy silently allows everything.

## The ledger

The ledger is a JSON file for each session under `~/.local/state/permission-slips/`, or under `PERMISSION_SLIPS_STATE`. The check hook denies write and shell calls whose text contains the ledger directory or a config path. The hook uses a text match. A shell can build the same path in a variable, write it from a script, or reach it through a symlink. For a stronger guarantee, put the ledger where the agent's sandbox cannot write and keep the hooks outside that sandbox.

```sh
export PERMISSION_SLIPS_STATE=/path/the/agent/cannot/write
```

## What the guard cannot see

The guard sees only tool calls that pass through hooks. An allowed command can run commands the guard never sees, such as a Makefile target that calls the deploy script. A tool with no matching rule passes. Rules match command text, so a guarded action reached by a different command, an encoded string, or another tool is not caught. Route each guarded action through one entry point and guard that entry point.

## The prompt

The issue hook trusts the prompt. Anything you paste into a prompt becomes part of it. An unquoted slip command pasted from somewhere else issues a slip. Quote or fence pasted text.

## Sessions

Slips use the session id that the host sends. They never cross sessions. `spend` without `PERMISSION_SLIPS_SESSION` ends matching slips in every session. That command can only take permission away.

## No config, broken config

Both hooks do nothing when no config file exists. When the config exists but is broken, the check hook denies every call. The issue hook exits with an error and issues nothing.

## In scope

Slips make your stated intent the gate for an action, and they stop an agent that drifts. If you need to stop an agent that is actively trying to get around them, also run it in a sandbox and keep the ledger outside it.

---

[← Prev](06-slips-you-could-write.md) (Slips you could write) | [Next →](claude-code.md) (Claude Code setup)
