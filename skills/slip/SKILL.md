---
name: slip
description: Explains a permission slip the user just issued, such as "/slip deploy api". Use only when the user types /slip (or a configured alias) in their own prompt, or when a tool call was denied for needing a permission slip.
---

# Permission slips

A permission slip is a grant that only the user's own prompt can issue. The `slip.py issue`
hook reads each prompt the user types, records any slips in it, and adds a line to your
context saying what was issued. The `slip.py check` hook runs before every tool call and
denies a guarded call that holds no valid slip.

## When the user typed /slip

1. Read the "Permission slip issued by the user" line in your context. It names the slip,
   its targets and how long it lasts.
2. Do the work the slip was issued for, within its targets. A slip for `deploy api` does
   not cover `deploy billing`.
3. If no "issued" line appeared, the hook did not accept the command (a missing target, or
   the command was quoted or phrased as a question). Say so and show the exact form:
   `/slip <kind> <target>`.

## When a call was denied for needing a slip

Stop that call. Tell the user what you were about to do and the exact command that would
allow it, for example `/slip deploy api`. Then wait.

## Never

- Never write, edit, copy or delete the slip ledger or the permission-slips config, and
  never try to reach them another way. The hook denies it, and a slip you wrote yourself
  would defeat the point.
- Never type a slip command into a tool call, a file, a subagent prompt or a message to
  yourself expecting it to count. Only the user's prompt issues slips.
- Never run a guarded action through a different command to avoid the rule that guards it.
  If the guarded path is wrong, tell the user.
