---
name: retro
description: "Retrospective over a repo's recent agent sessions: find recurring friction and propose environment fixes."
disable-model-invocation: true
---

The user has asked for a **retrospective**: read what agent sessions in this repo went through, and propose changes to the agent's **environment** (docs, skills, checks, hooks, tools) so future runs go better. A friction that recurs across sessions is worth more than a dramatic one-off, so this reads many sessions, not one.

You propose; you change nothing. The user picks what to act on, and that work goes through the repo's normal implementation workflow.

## Steps

1. If a `writing-for-agents` skill is available, load it: its levers (context pointers, no-ops, leading words, the two loads) are how you judge steering files and word your proposals.

2. **Scope.** Run, from the repo:

   ```
   python3 -I <this-skill-dir>/scripts/sessions.py
   ```

   It prints the repo, the window (since the last retro's `retro-window:` line, else 14 days) and one row per session with friction counters (errors, interrupts, oversized outputs, compactions). The user's own scope wins: pass `--since DATE` or `--days N`, or, when they name a single session ("this session"), read that one directly and skip step 3. State the scope back in one line (repo, window and where it came from, sessions found, noise skipped) and continue.

3. **Fan out.** Hand the sessions to parallel subagents in the **Miners** role of `~/.agents/workflow/agents/models.md`, each with [`MINING.md`](MINING.md) as its brief, the path to `scripts/sessions.py`, and its slice: about 4 sessions or 10 MB of transcript each, one subagent per session over 10 MB, at most 8 subagents. When the window holds more than that, take the sessions with the most user turns and errors and say how many went unread. The transcripts stay with the subagents; you work from their returns. Done when every session in scope has a returned block.

4. **PR record**, only when the user asks for it: for PRs merged in the window, `gh` their bot review comments and failed checks. A review finding or CI failure that recurs is a check that could have run before the push.

5. **Spot-check** the miners before using them: for every block, open the transcript at one cited line and confirm the quote is there and says what the block claims. A block that fails is re-mined or dropped, and the report says which.

6. **Cluster** the returned friction into **findings**: one finding per root cause, however many sessions show it. Rank by recurrence first (sessions affected), then cost (a lost session or a shipped bug outranks a slow search). Done when every friction event sits in a finding or is set aside as a one-off with no environment cause.

7. **Verify** each finding against the environment before proposing anything. Read the repo's always-loaded files (`AGENTS.md`/`CLAUDE.md`, skill descriptions), its check commands (package scripts, lint config, hooks, CI), and the user's global ones. Classify the finding as **missing**, **unwired** (exists, nothing runs it), **weak** (exists, worded so it does not fire), or **ignored** (exists, fires, broken anyway). Check `git log` on the files involved: a fix landed inside the window is **holding** if later sessions are clean, **recurring** if they are not.

8. **Sweep** the always-loaded files for **no-ops** (instructions the current model already follows without being told), stale lines, and meaning duplicated across files. Everything there costs context on every turn. A line is a no-op when a session that broke it is nowhere in the window: propose cutting it, and say which sessions you checked.

9. **Report** to the contract below and stop.

## Categories

Every finding gets one.

- **Navigation**: the agent searched long for a file or fact. Fix with a pointer where the agent will look, worded with the trigger it needed.
- **Checks**: a mistake a lint rule, type, test, or hook could have caught. Look for the existing check first: one that exists but sits unwired or broken is the finding.
- **Standards**: a judgement-call mistake review should have caught. Rules belong to the reviewer, who has a diff and no context pressure; the implementing agent carries only what it needs to write the code.
- **Steering**: a skill or `AGENTS.md` line that is missing, weak, in the wrong place, or bloated; an instruction the user keeps repeating.
- **Tool economy**: oversized outputs, wasteful reads, a CLI or MCP whose output is mostly noise.
- **Harness**: permission prompts, hooks, or sandboxing that stalled legitimate work, or let through what they should block.
- **Information access**: something the agent needed and could not reach (logs, a service, prod state).

## Fix ladder

Propose each fix at the highest level that makes it durable, highest first:

1. Architecture: change the code or the tooling so the mistake cannot be written (a type that cannot hold the bad value, a module that owns the only path).
2. A type or lint rule whose message names the fix, or a hook. Every **mechanical** finding (a fixed pattern, a banned call, a file-location rule) lands here or above.
3. A test or CI job that goes red on the mistake.
4. A tool or script change: better output, a missing command.
5. Sharper wording on an existing pointer or rule.
6. New doc or skill content, reached by a pointer.
7. A new always-loaded line, only for what every task needs.

Every rule a finding touches gets its **enforcer**: the check, hook or test that catches a break, or "none". A rule with no enforcer whose break recurs counts as a recurring finding even when the wording was sharpened in between; the report's proposal is the enforcer.

## Report contract

```
# Retro: <repo> · <from>..<to>
Sessions: <N read> of <N found> (<M noise skipped>, <K unread>) · sources: transcripts[, PR record]

## Findings
### 1. <title>
<category> · <missing|unwired|weak|ignored> · <n sessions>, <cost>
Evidence: <session ids with dates>; "<one short quote>"
Proposal: <file, and the change drafted at its ladder level>

## Earlier fixes
- <fix, commit or PR> · holding | recurring (<sessions>)

## Deletions
- <file:line> · no-op | stale | duplicate of <file:line>

## One-offs
- <one line each, no proposal>

retro-window: <from>..<to>
```

Up to 10 findings; the rest go to one-offs as single lines. Leave a section out when it is empty. Use the exact ISO timestamps from step 2 in the final line: the next retro starts its window from it.
