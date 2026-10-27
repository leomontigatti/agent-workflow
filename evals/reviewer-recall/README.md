# Reviewer recall

How many known bugs each correctness reviewer catches. The `## Review` records on our PRs count
what a reviewer found and never what it missed, so they cannot say which models
[`agents/models.md`](../../agents/models.md) needs for correctness. This eval measures misses.

Each case in [`cases.json`](cases.json) is a bug a correctness reviewer found on a real PR and a
later commit fixed. `run.py` checks out the commit before the fix and hands each model the prompt
`implement` step 5 gives a correctness reviewer: the reviewer brief, the diff and commit list, the
PR title as the intent, and [`CORRECTNESS.md`](../../skills/code-review/CORRECTNESS.md)'s brief
with the project's hotspots at that commit. A judge model then decides whether each review reports
the case's bug.

```sh
python3 -I evals/reviewer-recall/run.py review --models opus,sol,luna --repeats 2
python3 -I evals/reviewer-recall/run.py grade  ~/.local/state/reviewer-recall/<date>
python3 -I evals/reviewer-recall/run.py report ~/.local/state/reviewer-recall/<date>
```

Run it when a model in `agents/models.md` changes. Results
stay outside the repo; the conclusion goes into `agents/models.md`.

Reviews run at the correctness role's effort, medium. To measure another effort, pass
`--effort high` with a new directory: a directory holds one effort, and refuses another. To ask
whether a change turns misses into catches, rerun only the cases each model missed
(`--models sol --cases id,id`), one repeat first: it spares the Codex quota, which a full run at
high effort can exhaust.

## Reading the numbers

- **Every case was caught once.** A model that found a case in production found it at least once.
  Read a model's recall on the cases the other family first found (the `first found by` column).
- **Two runs per model is a small sample.** A case caught 1 of 2 times is a coin flip, not a
  property of the model.
- **The judge can be wrong.** Before acting on a surprising number, read the reviews behind it.
  Each one is `<case>.<model>.<run>.md` beside its verdict.
- **The intent is the PR title only.** The PR body records the fix, so it would leak the answer.

## Adding a case

A case needs the commit the reviewer saw (`before`), the PR's merge-base (`base`), the fix commit,
and a one-sentence bug a grader can match against a review: what goes wrong, and where. Take it
from a `## Review` line that names a fixed finding, and confirm the bug in the fix's diff.
