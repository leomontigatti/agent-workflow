# Ask triage

Whether a model rules on a found race or edge case the way the user did. `implement` step 2 lets
the agent **drop** an unlikely, loud one and sends the rest to the user as an **ask**; this eval
replays issues the user already ruled on through that rule, to see who drops what the user
dropped and who drops what the user went on to fix.

Each case in [`cases.json`](cases.json) is an issue and its ruling: `drop` when the user closed it
as not planned, `ask` when they fixed it, parked it or kept it open as worth raising, `null` when
they have not ruled. `run.py` checks out the default branch as it stood when the issue was opened and hands each model the
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
- **Few cases are drops, and most share a source.** Six of the eight are from one rubens audit,
  so a model's score on them moves a lot with one ruling and leans on how that audit wrote. Read
  the replies, `<repo>-<issue>.<model>.<run>.md`.
- **An audit's issue carries its finder's weighing.** Rubens #405 to #418 state the actors, the
  window and the cost of a hit under `## Weighing`, which a person's issue may leave for the model
  to find: read them as the easier cases.
- **The unruled cases have no score.** Their rows show how each model rules, for the user to
  compare with their own call.
- **An issue is an ask that was already raised.** What a session dropped in its thread never
  became one, so the cases lean towards the worth-raising side.

- **The checkout can lack the code.** An issue filed from a branch names code the default branch
  gained only when that branch merged. A model that verifies before it rules (Sol) then asks for
  want of the code, where one that rules from the issue's text does not: read such a reply before
  counting it.

## Adding a case

An issue for a race or an edge case found beside other work, whose body states the problem and not
the ruling: the body is cut at a `Wake-up trigger` or a `Recommendation` heading (the filer's own
pick), and comments are never read. Take the
ruling from how the user closed it, not from its labels at filing.
