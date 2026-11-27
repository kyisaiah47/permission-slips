[← Back to README](../README.md)

# How I use them

I run these slips on my own machine every day across many repos with both Claude Code and Codex. I leave out names, accounts and paths. Each section gives the slip, how it ends and the incident that made it necessary.

## Deploy named repos

`/force-deploy <repo> [<repo>...]`

This slip ships the repos named after the command. One guarded script runs each repo's deploy. A scheduled nightly deploy is the standing authorization. This slip ships something before that deploy.

- **Ends:** The slip remains valid until it is spent. A build failure, a refused attempt, a failed upload or a failed post-deploy check keeps the slip for repair and retry. The deploy wrapper spends it after live verification succeeds. A repo that shipped needs a new slip next time. An unrelated later prompt adds its own scope and never resets an existing slip.
- **Why:** Deploys fail for ordinary reasons. A slip that vanished after the first failure would require another approval for work already approved. An early parser also missed a command written inline at the end of a sentence. The command now counts anywhere in a prompt.

## Deploy everything

`/deploy-all`

This slip ships every repo through the same sweep as the nightly deploy, on demand.

- **Ends:** The slip remains valid until every fix I requested in the session is finished, verified and committed. The sweep then runs once.
- **Why:** The command originally ran as soon as it was typed. It now works like the deploy slip. It grants permission to ship everything, rather than ordering an immediate deploy, so a half-finished state never ships repo by repo.

## Arm ad campaigns

`/force-ads <platform> <campaign> [<campaign>...]`

This slip arms the named campaigns on one named ad platform. Each placement tier, such as video or short-form, has its own scope. A slip for one tier never covers another.

- **Ends:** The slip remains valid until the campaign is armed and its settings are read back, and for at most 24 hours. A failed arm keeps the slip. Pausing needs no slip.
- **Why:** Turning on a campaign spends money. The conversation and dry run establish the budget, dates and creative. The slip is the separate act of saying go.

## More than one subagent

`/allow-multi-agents`

This slip lifts the cap of one subagent per prompt.

- **Ends:** This package uses a prompt slip. I have also run the slip for the whole session, which suits days spent fanning work out.
- **Why:** One prompt asking for a new page in seven repos started seven agents at once. An instruction stating the cap did not stop them. The hook stopped them after one more fix. Parallel calls in one turn could not see each other, so the cap moved to a locked per-session state file that fails closed.

## A design brief

`/allow-design-brief`

This slip lets one subagent brief carry design direction, including colours, palettes, typefaces, named looks or reference sets.

- **Ends:** The slip is spent on one brief. The next brief is checked again. Typing it twice issues two slips.
- **Why:** Subagent briefs received design direction without my approval, and the work drifted. Now a brief may carry only direction I approved in the conversation. The slip lets that one brief through.

Each slip follows four rules. Only my typed prompt issues it. It names its target. It ends on a defined condition. A hook outside the model checks it.

---

[← Prev](04-checked-at-the-door.md) (4. Checked at the door) | [Next →](06-slips-you-could-write.md) (Slips you could write)
