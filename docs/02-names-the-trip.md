[← Back to README](../README.md)

# 2. Names the trip

*Every slip is scoped to a named target.*

A repo mentioned near a command is not a repo named by that command. Deploy and ad slips cover only the names written after the command. Nearby product mentions do not count. The agent never infers extra repos or campaigns from the conversation.

## The rule

The words after the command are the slip's targets. A rule's regex pulls the target from the tool call through a named group, `target`. The call is allowed only when a valid slip of that kind lists the target.

```json
{
  "name": "production deploy",
  "tool": "^(Bash|exec_command)$",
  "pattern": "(?:^|[\\s;&|])(?:\\./)?scripts/deploy\\.sh\\s+(?P<target>[A-Za-z0-9_.-]+)",
  "slip": "deploy"
}
```

```python
def covers(slip, target):
    return target is None or not slip["targets"] or target in slip["targets"]
```

## Reading targets from the prompt

Targets stop at the first word that is not target-shaped, at a stop word such as `and`, `then` or `after`, or at the end of the sentence. `/force-deploy api web after the fix` names two targets, `api` and `web`.

```python
STOP_WORDS = {"and", "then", "after", "afterwards", "please", "when", "once", "if", "so", "to", "for"}
TARGET = re.compile(r"^[A-Za-z0-9_.:/@-]+$")
```

Set `needs_target` on a kind to skip slips without targets. A rule can also set a fixed `target`, as the package publish rule does with `registry`, when the command line carries no name.

```json
"deploy":  { "lifetime": "until-spent", "needs_target": true, "aliases": ["force-deploy"] },
"publish": { "lifetime": "once",        "needs_target": true }
```

A slip with no targets covers any target of its kind. This applies to kinds such as `agents`, which have nothing to name. It also explains why `needs_target` exists for kinds that require a target.

---

[← Prev](01-signed-by-the-human.md) (1. Signed by the human) | [Next →](03-good-for-one-trip.md) (3. Good for one trip)
