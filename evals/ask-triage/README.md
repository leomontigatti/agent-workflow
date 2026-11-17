# Ask triage

Whether a model rules on a found race or edge case the way the user did. `implement` step 2 lets
the agent **drop** an unlikely, loud one and sends the rest to the user as an **ask**; this eval
replays issues the user already ruled on through that rule, to see who drops what the user
dropped and who drops what the user went on to fix.

Each case in [`cases.json`](cases.json) is an issue and its ruling: `drop` when the user closed it
as not planned, `ask` when they fixed or parked it, `null` when they have not ruled. `run.py`
checks out the default branch as it stood when the issue was opened and hands each model the
issue's title and body with step 2's rule, read from this checkout, so a reworded rule is measured
by rerunning.

```sh
python3 -I evals/ask-triage/run.py rule --models opus:medium,fable:low --repeats 2
python3 -I evals/ask-triage/run.py report ~/.local/state/ask-triage/<date>
```

Run it when step 2's rule changes, or to weigh a model as the one that rules. Results stay outside
the repo.

## Reading the numbers

- **The two errors differ in cost.** Raising what the user dropped costs them one ask; dropping
  what the user fixed hides a bug. Read the second number first.
- **Few cases are drops.** The user closes few issues as not planned, so a model's score on them
  moves a lot with one ruling. Read the replies, `<repo>-<issue>.<model>.<run>.md`.
- **The unruled cases have no score.** Their rows show how each model rules, for the user to
  compare with their own call.
- **An issue is an ask that was already raised.** What a session dropped in its thread never
  became one, so the cases lean towards the worth-raising side.

## Adding a case

An issue for a race or an edge case found beside other work, whose body states the problem and not
the ruling: the body is cut at a `Wake-up trigger` heading, and comments are never read. Take the
ruling from how the user closed it, not from its labels at filing.
