[← Back to README](../README.md)

# 1. Signed by the human

*Only a prompt you type issues a slip.*

A grant the agent can produce is not a grant. In my own setup, grants are read only from prompts I type or queue. Tool results, subagent transcripts, hook metadata and anything the agent writes never issue one, and the agent can never write or reconstruct the grant ledger.

## The rule

A slip is issued only by the `UserPromptSubmit` hook from the text of a prompt you submitted. Tool output, files the agent reads, subagent briefs and the agent's own messages never pass through that hook. Nothing the agent writes can issue a slip.

```json
"UserPromptSubmit": [
  { "hooks": [ { "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/slips/slip.py\" issue", "timeout": 10 } ] }
]
```

## Mentions are not slips

Typing about a slip does not issue one. The parser skips commands inside questions, commands after negations and quoted content, including code fences, inline code, lines starting with `>` and double-quoted strings. The parser also skips a slip that needs a target when the slip has no target.

| Prompt | Issues a slip? |
|--------|----------------|
| `fix the login bug, then /slip deploy api` | yes |
| `/force-deploy api web after the fix` | yes, for `api` and `web` |
| `should I /slip deploy api?` | no, a question |
| `don't /slip deploy api yet` | no, a negation |
| ``the command is `/slip deploy api` `` | no, inline code |
| `> /slip deploy api` | no, a quoted line |
| `he typed "/slip deploy api" yesterday` | no, a quoted string |
| `/slip deploy` | no, `deploy` needs a target |

My grant parsers skip all of these cases. Asking whether to deploy, telling the agent not to deploy yet and pasting an example command do not issue grants.

```python
def strip_quoted(prompt):
    """Text that only mentions a slip does not issue one: code fences, inline code,
    quoted lines and double-quoted strings are removed before parsing."""
    text = re.sub(r"```.*?```", " ", prompt, flags=re.S)
    text = re.sub(r"`[^`]*`", " ", text)
    text = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith(">"))
    return re.sub(r"\"[^\"\n]*\"", " ", text)
```

A command written inline counts. An earlier deploy-parser version missed a command at the end of a sentence. The command now counts anywhere in a prompt when it is not quoted, negated or asked.

## What the agent sees

When a slip is issued, the hook prints one line. The host adds that line to the agent's context so the agent knows what it may do:

```text
Permission slip issued by the user: deploy (api), good until it is spent.
```

The agent cannot write the ledger or the config. The check hook denies any write or shell call whose text names the state directory or a config path.

```python
def protects_itself(tool, tool_input, cfg_path):
    """The agent may not write the ledger or the config. A slip it could write itself
    would not be a slip."""
    guarded = [str(state_dir()), str(cfg_path), ".permission-slips.json", "permission-slips/config.json"]
    blob = call_text(tool, tool_input) if SHELL_TOOLS.match(tool) else json.dumps(tool_input)
    if not (SHELL_TOOLS.match(tool) or WRITE_TOOLS.match(tool)):
        return None
    for g in guarded:
        if g and g in blob:
            return ("This call touches the permission-slip ledger or config. Only the hooks "
                    "write those. Ask the user to issue the slip instead.")
    return None
```

---

[Next →](02-names-the-trip.md) (2. Names the trip)
