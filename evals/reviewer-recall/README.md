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
python3 -I evals/reviewer-recall/run.py review --models fable:low,opus:medium --out ~/.local/state/reviewer-recall/<dir>
python3 -I evals/reviewer-recall/run.py grade  ~/.local/state/reviewer-recall/<date>
python3 -I evals/reviewer-recall/run.py report ~/.local/state/reviewer-recall/<date>
```

Run it when a model in `agents/models.md` changes, or to weigh a candidate for a role. Results
stay outside the repo; the conclusion goes into `agents/models.md`.

Reviews run at the correctness role's effort, medium, or at `--effort`. A model may name its own:
`--models fable:low,opus:medium` compares Fable at low with Opus at medium in one directory, so the
per-case table and the `a+b` union lines cover both. A directory holds one effort per model and
refuses another: to measure Opus at high too, use a new directory. To ask
whether a change turns misses into catches, rerun only the cases each model missed
(`--models sol --cases id,id`), one repeat first: it spares the Codex quota, which a full run at
high effort can exhaust.

## A brief change: the lifetime lens

[`briefs/lifetime.md`](briefs/lifetime.md) is `CORRECTNESS.md`'s brief with a lifetime lens folded
in: for every async start in the diff, its premise, whether it still holds when it lands, and
whether what it acquired is given back on every exit. The question is whether the lens catches more
async lifetime bugs without costing the baseline the attention it takes from the brief's other
checks. Reviews run on Sol at medium, the correctness role's effort. Each of the four runs gets a
directory of its own, since a directory holds one brief on one case set:

```sh
r=~/.local/state/reviewer-recall
for cases in cases.json cases-lifetime.json; do
  python3 -I evals/reviewer-recall/run.py review --models sol --repeats 2 --cases-file $cases --out $r/current-$cases
  python3 -I evals/reviewer-recall/run.py review --models sol --repeats 2 --cases-file $cases --brief briefs/lifetime.md --out $r/lifetime-$cases
done
```

Then `grade` and `report` each directory. To spare the quota, run one repeat first, then repeat
only the cases each brief missed (`--cases id,id`). Two numbers decide it:

- **Recall on [`cases-lifetime.json`](cases-lifetime.json) should rise.** Those cases were found
  by the lifetime audit after the PRs that brought them in had merged, so they test what review
  missed: every one went through a correctness review, and only `rubens-issue283` and
  `rubens-issue302` were raised there (and parked). The current brief's recall there is the floor.
- **Recall on `cases.json` must hold.** A lens that gains lifetime bugs and loses the baseline's
  spent attention the brief's other checks needed.

A lifetime case has an `issue` and no `fix`: most are still open, and the grader matches the
`bug` sentence, taken from the issue.

**Not adopted yet.** The first run (2026-11-17, #142, one repeat) gave the lens 6 of 16 on
`cases-lifetime.json` against the current brief's 4 of 16. The `cases.json` half has not run, so
`CORRECTNESS.md` keeps the current brief until it has and recall there holds.

## Foresight: `consult`

`run.py consult` takes the same options and asks a different question: would the model have warned
of the bug before the change was written? It checks out the PR's merge-base, hands the model the PR
title, the linked issue's body and the paths the change went on to touch, and asks for at most 8
hazards; `grade` and `report` then read the directory as they read a review's. A directory holds
reviews or consults, never both.

On 2026-11-17 (two runs per case) Sol at medium warned of the bug in 18 of 28 consults, Fable at
low in 14 of 29 and Opus at medium in 13 of 30, at $1.21 a consult for Fable and $0.68 for Opus.
Every case is a bug the review caught anyway, so a consult moves a fix earlier and no more.

## Reading the numbers

- **Every case was caught once.** A model that found a case in production found it at least once.
  Read a model's recall on the cases the other family first found (the `first found by` column).
- **Two runs per model is a small sample.** A case caught 1 of 2 times is a coin flip, not a
  property of the model.
- **The judge can be wrong.** Before acting on a surprising number, read the reviews behind it.
  Each one is `<case>.<model>.<run>.md` beside its verdict.
- **The intent is the PR title only.** The PR body records the fix, so it would leak the answer.
- **Time is wall seconds per review**, from launch to exit, so it moves with `--jobs` and the
  provider's load that day: compare models measured in one run.
- **Cost is Claude's `total_cost_usd`**, the CLI's estimate at API list prices, not what a
  subscription bills. Codex reports tokens but no price, so its cost reads "not reported"; compare
  it on tokens. Each review's numbers are in `<case>.<model>.<run>.meta.json`; a review run
  before they were recorded has none, and the report counts how many were timed.

## Adding a case

A case needs the commit the reviewer saw (`before`), the PR's merge-base (`base`), and a
one-sentence bug a grader can match against a review: what goes wrong, and where. A case in
`cases.json` also names its fix commit: take it from a `## Review` line that names a fixed finding,
and confirm the bug in the fix's diff. A case in `cases-lifetime.json` starts from an issue the
audit filed instead: `git blame` the lines the issue names on the commit it was found at, take
the PR their squash commit names, and check that its head already has the bug.
