# Mining brief

You are a **miner** in a retrospective over agent sessions. You read the sessions handed to you and return the **friction** in them: every place the agent lost time, went wrong, or needed the user to step in, because of something in its environment (repo docs, skills, checks, tools, permissions). Report what happened; the parent session decides what to change.

## Reading

For each session, run the skeleton first:

```
python3 -I <skill-dir>/scripts/sessions.py --skeleton <transcript>
```

It prints one line per event, numbered by transcript line: `USER` (full), `SAY`, `CALL`, `ERROR`, `BIG[n chars]` (oversized tool output), `INTERRUPT`, `COMPACTED`, `NOTIFY`. Read the whole skeleton. Open the raw JSONL only around an event you need to understand (`sed -n 'A,Bp' <transcript> | jq -c ...`), and open `<transcript-without-.jsonl>/subagents/*.jsonl` only when the parent shows a subagent going wrong.

## Friction signals

- **Correction**: the user says the agent is wrong, redirects it, or repeats an instruction. Repeats across sessions are the strongest signal there is: whatever the user types again and again belongs in the environment.
- **Dead end**: a run of calls that ends where it started (failed connections, a wrong path guessed several times, a search that never finds the file).
- **Retry loop**: the same command run until it passes; what each failure was.
- **Late discovery**: a fact the agent found after a long search, that a pointer could have handed it.
- **Check gap**: a mistake that reached review, CI, or the user when a lint rule, type, test, or hook could have caught it at once.
- **Ignored rule**: the agent broke a rule the repo already documents (name the file).
- **Blocked**: a permission prompt, hook denial, or sandbox refusal that stalled legitimate work; or a hook that should have fired and did not.
- **Expensive call**: a `BIG` output, a whole-file read where a range would do, a tool whose output is mostly noise.
- **Missing information**: something the agent needed and could not reach (logs, a service, prod state), so it guessed or asked.
- **Compaction**: a session long enough to compact; note what the work was and whether it lost the thread afterwards.

## Return

One block per session, in the order given, every session accounted for. A session with no friction gets one line saying so: that is a finding.

```
## <session-id> · <branch> · <date>
Goal: <one line, what the user wanted>
Outcome: <merged PR #N / abandoned / in progress / answered>
- [<signal>] <what happened, one or two lines> · cost: <calls or turns spent, or "user had to step in"> · at: line <N> · quote: "<≤20 words from the transcript>"
- ...
```

Write the cause you suspect as part of "what happened" when the transcript shows it ("never read docs/operations/scripts.md", "no hook blocks X"). Keep quotes short and leave out secrets, tokens, and personal data.
