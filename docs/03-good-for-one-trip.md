[← Back to README](../README.md)

# 3. Good for one trip

*Every slip has a defined end.*

The slip determines its own end. My deploy slip outlives failed builds because a failure requires a fix and a retry. My subagent slip started as valid for one prompt and later changed to the whole session. A single design brief is spent on one call. Each kind selects its lifetime from what the slip does.

## The rule

Every slip kind declares one of four lifetimes. The guard checks the lifetime on every call. The ledger records when a slip was issued, which prompt issued it and whether it was spent.

| Lifetime | Ends when |
|----------|-----------|
| `once` | The slip is spent by the one call it allows. This lifetime suits a production migration or a package publish. |
| `prompt` | The slip remains valid for the prompt that issued it. The next prompt you submit ends it. This lifetime suits fanning out subagents for one request. |
| `session` | The slip remains valid until the session ends. Slips never cross sessions. This lifetime suits opening one outbound host while you work. |
| `until-spent` | The slip remains valid until something calls `slip.py spend`. Failures and retries keep it valid. This lifetime suits a deploy that ends only after live verification. |

```python
def valid(slip, current_prompt):
    if slip["spent"]:
        return False
    if slip["lifetime"] == "prompt" and slip["prompt"] != current_prompt:
        return False
    return True
```

## Spending

Your own code performs spending, not the agent's judgment. The deploy script calls `spend` after its health check passes. Without `PERMISSION_SLIPS_SESSION` set, spending ends matching slips in every session. The script therefore does not need to know which agent asked. A slip with several targets loses only the target that was spent.

```sh
target="$1"
./scripts/deploy.sh "$target"
curl -fsS "https://$target.example.com/health" >/dev/null   # verify it is live
python3 ~/.permission-slips/slip.py spend deploy "$target"
```

Spending can only take permission away. Anything can call it, including the agent.

## Free calls per prompt

A rule can allow a few calls per prompt without a slip. `free_per_prompt` sets the number of free calls. The count resets with each prompt. The example makes the first subagent in a prompt free, while later subagents need an `agents` slip.

```json
{ "name": "more than one subagent per prompt", "tool": "^(Agent|Task)$", "free_per_prompt": 1, "slip": "agents" }
```

## Parallel calls

Parallel tool calls in one turn each wait for an exclusive lock on the session ledger. Without the lock, parallel subagent calls in one turn could not see each other, and all calls could pass a one-per-prompt cap. The lock prevents two calls from spending the same once-slip.

```python
@contextmanager
def ledger(session):
    """The session's slips, under an exclusive lock. Parallel tool calls in one turn each wait
    their turn here, so two calls can never both spend the same once-slip."""
    d = state_dir()
    d.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session or "no-session")
    path = d / f"{safe}.json"
    with open(d / f"{safe}.lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
```

---

[← Prev](02-names-the-trip.md) (2. Names the trip) | [Next →](04-checked-at-the-door.md) (4. Checked at the door)
