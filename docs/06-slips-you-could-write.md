[← Back to README](../README.md)

# Slips you could write

Each idea below names a slip kind and a rule. The sketches use the config format from `slips/config.example.json`. Test each pattern against your real commands before relying on it.

## Production migration

One slip permits one production migration. The environment flag supplies the target.

```json
"slips": { "migrate": { "lifetime": "once", "needs_target": true } },
"rules": [ { "name": "production migration", "tool": "^(Bash|exec_command)$", "pattern": "\\b(?:prisma migrate deploy|supabase db push|rails db:migrate)\\b.*--env[= ](?P<target>prod\\w*)", "slip": "migrate" } ]
```

## Push to a protected branch

The guard matches a push to a protected branch. The slip names the branch.

```json
"slips": { "push": { "lifetime": "once", "needs_target": true } },
"rules": [ { "name": "push to protected branch", "tool": "^(Bash|exec_command)$", "pattern": "\\bgit push\\b.*\\s(?P<target>main|release/[\\w.-]+)\\b", "slip": "push" } ]
```

## Package publish

One slip permits one package publish. The target is fixed because the command carries no name worth matching.

```json
"slips": { "publish": { "lifetime": "once" } },
"rules": [ { "name": "package publish", "tool": "^(Bash|exec_command)$", "pattern": "\\b(?:npm publish|twine upload|cargo publish)\\b", "target": "registry", "slip": "publish" } ]
```

## Infrastructure

The guard covers infrastructure changes that are hard to undo, such as `terraform apply` or `kubectl delete`.

```json
"slips": { "infra": { "lifetime": "once", "needs_target": true } },
"rules": [ { "name": "infrastructure change", "tool": "^(Bash|exec_command)$", "pattern": "\\b(?:terraform apply|kubectl delete)\\b.*?(?:-var-file=|--context[= ])(?P<target>[\\w.-]+)", "slip": "infra" } ]
```

## Spend cap

A spend cap guards the script that raises a budget or starts paid work. The script reports success, and that result ends the slip.

```json
"slips": { "spend": { "lifetime": "until-spent", "needs_target": true } },
"rules": [ { "name": "paid work", "tool": "^(Bash|exec_command)$", "pattern": "scripts/raise-budget\\.sh\\s+(?P<target>[\\w.-]+)", "slip": "spend" } ]
```

## Read one secret

One slip permits one secret read. The guard names the key in the secret manager command, so a slip for one key cannot cover another.

```json
"slips": { "secret": { "lifetime": "once", "needs_target": true } },
"rules": [ { "name": "secret read", "tool": "^(Bash|exec_command)$", "pattern": "\\b(?:op read|vault kv get|bw get)\\b.*?(?P<target>[A-Z][A-Z0-9_]+)", "slip": "secret" } ]
```

## Send one message

One slip permits one message send. The guard checks the send command, so an agent can draft freely but can send only what you allowed.

```json
"slips": { "send": { "lifetime": "once", "needs_target": true } },
"rules": [ { "name": "outbound message", "tool": "^(Bash|exec_command)$", "pattern": "scripts/send\\.sh\\s+(?P<target>[\\w.-]+)", "slip": "send" } ]
```

## One outbound host

One egress slip permits access to one outbound host for the session. Outbound access stays closed by default. This reopens the external-communication leg of the lethal trifecta for that named host.

```json
"slips": { "egress": { "lifetime": "session", "needs_target": true } },
"rules": [ { "name": "outbound request", "tool": "^(Bash|exec_command)$", "pattern": "\\b(?:curl|wget)\\b[^|;&]*?https?://(?P<target>[A-Za-z0-9.-]+)", "slip": "egress" } ]
```

## New dependency

One slip permits one new dependency. The guard checks package installs, so new packages arrive only when you name them.

```json
"slips": { "deps": { "lifetime": "prompt", "needs_target": true } },
"rules": [ { "name": "dependency install", "tool": "^(Bash|exec_command)$", "pattern": "\\b(?:npm install|pnpm add|pip install)\\s+(?P<target>[@\\w./-]+)", "slip": "deps" } ]
```

## Delete a path

One slip permits deletion of one path. The guard checks recursive deletes and names the path that may go.

```json
"slips": { "rm": { "lifetime": "once", "needs_target": true } },
"rules": [ { "name": "recursive delete", "tool": "^(Bash|exec_command)$", "pattern": "\\brm\\s+-[a-zA-Z]*r[a-zA-Z]*\\s+(?P<target>[\\w./-]+)", "slip": "rm" } ]
```

## Two people, or no one typing

A team can require two people to issue one slip. The issue hook records the slip only after a second named person also issues it. This repo does not ship that behavior, but the ledger format leaves room for it.

CI can use an issuer that a human controls when nobody is typing. The issuer can be a pull-request label, a protected-environment approval, or a signed tag. The rule stays the same. The issuer must remain outside the agent's reach.

> [!NOTE]
> Patterns match command text. Write each pattern so the guarded action is reachable only through the matched command, such as a script that receives all deploys.

---

[← Prev](05-how-i-use-them.md) (How I use them) | [Next →](threat-model.md) (Threat model)
