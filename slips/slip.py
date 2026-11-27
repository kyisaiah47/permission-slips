#!/usr/bin/env python3
"""Permission slips for coding agents.

A permission slip is a grant that only a prompt you type can issue. It names what it unlocks,
it ends on a defined condition, and a hook outside the model checks it before the tool call runs.

    slip.py issue           UserPromptSubmit hook: reads your prompt, records any slips in it
    slip.py check           PreToolUse hook: denies a guarded tool call that holds no valid slip
    slip.py spend KIND [T]  ends an until-spent slip (call it from your own script after success)
    slip.py list            prints the slips held by a session (needs PERMISSION_SLIPS_SESSION)

Works with Claude Code and Codex. Both send the same hook JSON on stdin and read the same
PreToolUse deny response. Standard library only, Python 3.8+.
"""
import fcntl
import json
import os
import re
import sys
import time
from contextlib import contextmanager
from pathlib import Path

LIFETIMES = ("once", "prompt", "session", "until-spent")
NEGATIONS = {"don't", "dont", "do", "not", "never", "no", "without", "skip"}
STOP_WORDS = {"and", "then", "after", "afterwards", "please", "when", "once", "if", "so", "to", "for"}
TARGET = re.compile(r"^[A-Za-z0-9_.:/@-]+$")
WRITE_TOOLS = re.compile(r"^(Write|Edit|MultiEdit|NotebookEdit|apply_patch)$")
SHELL_TOOLS = re.compile(r"^(Bash|exec_command|shell|local_shell)$")


# ---------------------------------------------------------------- paths and config

def state_dir():
    return Path(os.environ.get("PERMISSION_SLIPS_STATE") or
                Path.home() / ".local" / "state" / "permission-slips")


def config_path(cwd=None):
    env = os.environ.get("PERMISSION_SLIPS_CONFIG")
    if env:
        return Path(env)
    project = Path(cwd or os.getcwd()) / ".permission-slips.json"
    if project.exists():
        return project
    return Path.home() / ".config" / "permission-slips" / "config.json"


def load_config(cwd=None):
    path = config_path(cwd)
    cfg = json.loads(path.read_text())
    slips = cfg.get("slips") or {}
    for kind, spec in slips.items():
        life = spec.get("lifetime", "once")
        if life not in LIFETIMES:
            raise ValueError(f"slip {kind!r}: lifetime must be one of {', '.join(LIFETIMES)}")
    for rule in cfg.get("rules") or []:
        if rule.get("slip") not in slips:
            raise ValueError(f"rule {rule.get('name')!r} names unknown slip {rule.get('slip')!r}")
        re.compile(rule.get("tool", ".*"))
        if rule.get("pattern"):
            re.compile(rule["pattern"])
    return cfg, path


# ---------------------------------------------------------------- the ledger

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
        try:
            data = json.loads(path.read_text()) if path.exists() else {}
        except ValueError:
            data = {}
        data.setdefault("prompt", 0)
        data.setdefault("slips", [])
        data.setdefault("free", {})
        yield data
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(path)


# ---------------------------------------------------------------- issuing

def strip_quoted(prompt):
    """Text that only mentions a slip does not issue one: code fences, inline code,
    quoted lines and double-quoted strings are removed before parsing."""
    text = re.sub(r"```.*?```", " ", prompt, flags=re.S)
    text = re.sub(r"`[^`]*`", " ", text)
    text = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith(">"))
    return re.sub(r"\"[^\"\n]*\"", " ", text)


def parse_slips(prompt, cfg):
    """Every slip command in the prompt, as (kind, [targets]).

    Accepted forms:  /slip deploy api web   or an alias such as   /force-deploy api
    Skipped:  a command in a question, a command after a negation ("don't /slip deploy"),
    and anything quoted. Targets are the words right after the command, up to the first
    word that isn't target-shaped, a stop word, or the end of the sentence."""
    slips = cfg.get("slips") or {}
    alias = {}
    for kind, spec in slips.items():
        for a in spec.get("aliases") or []:
            alias[a.lower()] = kind
    found = []
    text = strip_quoted(prompt)
    for sentence in re.split(r"(?<=[.!?;])\s+|\n+", text):
        if sentence.rstrip().endswith("?"):
            continue
        words = sentence.split()
        for i, w in enumerate(words):
            if not w.startswith("/"):
                continue
            name = w[1:].rstrip(",.;:!").lower()
            rest = words[i + 1:]
            if name == "slip":
                if not rest:
                    continue
                kind = rest[0].rstrip(",.;:!").lower()
                rest = rest[1:]
            elif name in alias:
                kind = alias[name]
            else:
                continue
            if kind not in slips:
                continue
            before = {x.lower().strip(",.") for x in words[max(0, i - 2):i]}
            if before & NEGATIONS:
                continue
            targets = []
            for t in rest:
                end = t.endswith((".", ";", ":", "!"))
                t = t.rstrip(",.;:!")
                if not t or t.lower() in STOP_WORDS or not TARGET.match(t) or t.startswith("/"):
                    break
                targets.append(t)
                if end:
                    break
            if slips[kind].get("needs_target") and not targets:
                continue
            found.append((kind, targets))
    return found


def describe(kind, targets, life):
    scope = ", ".join(targets) if targets else "any target"
    end = {"once": "good for one call", "prompt": "good for this prompt",
           "session": "good for this session", "until-spent": "good until it is spent"}[life]
    return f"{kind} ({scope}), {end}"


def cmd_issue(event):
    if not config_path(event.get("cwd")).exists():
        return 0
    cfg, _ = load_config(event.get("cwd"))
    prompt = str(event.get("prompt") or "")
    session = event.get("session_id")
    issued = []
    with ledger(session) as data:
        data["prompt"] += 1
        data["free"] = {}
        for kind, targets in parse_slips(prompt, cfg):
            life = cfg["slips"][kind].get("lifetime", "once")
            data["slips"].append({"kind": kind, "targets": targets, "lifetime": life,
                                  "prompt": data["prompt"], "issued": time.time(),
                                  "spent": False})
            issued.append(describe(kind, targets, life))
    if issued:
        # Added to the model's context, so the agent knows what it may now do.
        print("Permission slip issued by the user: " + "; ".join(issued) + ".")
    return 0


# ---------------------------------------------------------------- checking

def call_text(tool, tool_input):
    if isinstance(tool_input, dict):
        for key in ("command", "cmd"):
            if isinstance(tool_input.get(key), str):
                return tool_input[key]
        if isinstance(tool_input.get("command"), list):
            return " ".join(map(str, tool_input["command"]))
    return json.dumps(tool_input, ensure_ascii=False)


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


def valid(slip, current_prompt):
    if slip["spent"]:
        return False
    if slip["lifetime"] == "prompt" and slip["prompt"] != current_prompt:
        return False
    return True


def covers(slip, target):
    return target is None or not slip["targets"] or target in slip["targets"]


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))
    return 0


def cmd_check(event):
    tool = str(event.get("tool_name") or "")
    tool_input = event.get("tool_input") or {}
    if not config_path(event.get("cwd")).exists():
        return 0  # not set up here: the hook stays out of the way
    try:
        cfg, cfg_path = load_config(event.get("cwd"))
    except Exception as e:  # fail closed: a broken policy guards everything until it's fixed
        return deny(f"permission-slips config could not be read ({e}). Fix the config first.")
    reason = protects_itself(tool, tool_input, cfg_path)
    if reason:
        return deny(reason)
    text = call_text(tool, tool_input)
    for rule in cfg.get("rules") or []:
        if not re.search(rule.get("tool", ".*"), tool):
            continue
        target = rule.get("target")
        if rule.get("pattern"):
            m = re.search(rule["pattern"], text)
            if not m:
                continue
            target = m.groupdict().get("target") or target
        kind = rule["slip"]
        with ledger(event.get("session_id")) as data:
            free = int(rule.get("free_per_prompt", 0))
            key = rule.get("name", kind)
            if free and data["free"].get(key, 0) < free:
                data["free"][key] = data["free"].get(key, 0) + 1
                continue
            held = [s for s in data["slips"]
                    if s["kind"] == kind and valid(s, data["prompt"]) and covers(s, target)]
            if not held:
                what = f"{kind} {target}" if target else kind
                return deny(f"{rule.get('name', kind)} needs a permission slip. Only the user can "
                            f"issue one, by typing: /slip {what}")
            slip = held[0]
            if slip["lifetime"] == "once":
                slip["spent"] = True
    return 0


# ---------------------------------------------------------------- spending and listing

def sessions(session):
    if session:
        return [session]
    d = state_dir()
    return [p.stem for p in d.glob("*.json")] if d.exists() else []


def cmd_spend(session, kind, target=None):
    """Ends until-spent slips. Without PERMISSION_SLIPS_SESSION it ends them in every session,
    so a deploy script can call it without knowing which agent session asked. Spending can only
    take permission away, so it is safe for anything to call."""
    n = 0
    for sid in sessions(session):
        n += _spend_one(sid, kind, target)
    print(f"spent {n} slip(s)")
    return 0


def _spend_one(session, kind, target):
    n = 0
    with ledger(session) as data:
        for s in data["slips"]:
            if s["kind"] == kind and not s["spent"] and covers(s, target):
                if target and s["targets"] and len(s["targets"]) > 1:
                    s["targets"] = [t for t in s["targets"] if t != target]
                else:
                    s["spent"] = True
                n += 1
    return n


def cmd_list(session):
    with ledger(session) as data:
        live = [s for s in data["slips"] if valid(s, data["prompt"])]
        for s in live:
            print(describe(s["kind"], s["targets"], s["lifetime"]))
        if not live:
            print("no slips held")
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd in ("issue", "check"):
        try:
            event = json.load(sys.stdin)
        except ValueError:
            event = {}
        return cmd_issue(event) if cmd == "issue" else cmd_check(event)
    session = os.environ.get("PERMISSION_SLIPS_SESSION")
    if cmd == "spend" and len(argv) >= 3:
        return cmd_spend(session, argv[2], argv[3] if len(argv) > 3 else None)
    if cmd == "list":
        return cmd_list(session)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
