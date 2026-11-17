---
name: lifetime-audit
description: "Hunt a project's code for async lifetime bugs (stale responses, unreleased claims, blind writes), prove each with a failing test, and file them."
disable-model-invocation: true
---

# Lifetime audit

Every async start (a request, an await, a timer, a queued job, an acquired resource, a read a
later write depends on) has a **lifetime**: it starts under a premise and lands later, when the
premise may be gone. A **stale response** applies an answer about a state that has since changed;
an unreleased claim outlives the code that took it, a throw included; a **blind write** sets a
state it read earlier without checking that it still holds. This audit cuts a project's code into
slices, has one judge read each slice with the lifetime question, and files only what a separate
prover turns **red**.

Each judge also names the **shape** of the state it read: whether its states and transitions are
explicit. A shape worth fixing is reported beside the bugs.

Run it in a thread on the project whose checkout is at `origin/<default>`. The audit writes nothing
to the project; the issues it files are its output.

## Steps

1. **Commit.** `git fetch`, and check that `HEAD` is `origin/<default>`; when it is not, switch
   this thread's checkout to it (`git switch --detach origin/<default>`). Note the short sha: the
   scan, the judges and the provers all read this checkout. Read `AGENTS.md` for where the
   sources, the schema and the tests live.

2. **Slice.** Run
   `python3 -I ~/.agents/workflow/skills/lifetime-audit/scripts/scan.py <checkout> --skip <state>`,
   where `<state>` is `~/.local/state/lifetime-audit/<repo>.json` (`<repo>` the GitHub
   `owner-name`; a missing file skips nothing). It puts every source file not judged before and
   unchanged since into one slice of at most 1,500 lines (a longer file in a slice of its own),
   highest lifetime score first, and lists
   the explicit lifecycles and the lifecycle writes. The score orders the slices; every slice is
   judged. For a stack the script does not read, cut the slices by hand the same way.

   Tell the user the plan: files, lines, slices, and one judge per slice. Up to 20 slices, go on.
   Past 20, wait for their go-ahead, offering a narrower first run with `--under <dir>` on the
   directories with the highest-scoring slices; the state file carries the rest to later runs.

   Done when the slices are fixed and, past 20, the user agreed to them.

3. **Judge.** Spawn one judge per slice, all in one message: a `delegate_task` child in the
   Lifetime judges role of `~/.agents/workflow/agents/models.md` (outside T3, its fallback), in
   this checkout. The task reads: "Read `~/.agents/workflow/skills/lifetime-audit/JUDGE.md` and
   follow it. Checkout `<path>` at `<sha>`. Slice `<n>`:" followed by the slice's lines from the
   scan, each file with its score and signals.

   Done when every judge has reported. A judge that fails or returns nothing is spawned once
   more, fresh; a second failure leaves its slice unjudged, named in the report.

4. **Rule.** Take every `traced` or `suspected` bug the judges did not mark `tracked`, and merge
   claims with one cause into one. Weigh each as `~/.agents/workflow/skills/implement/SKILL.md`
   step 2 weighs a race or an edge case it finds, from the judge's likelihood and backstop: a
   **drop** (loud and unlikely) is one line in the report and ends there; every other claim is an
   **ask**. Ruling comes before proving, so no prover runs on a drop.

   Done when every claim is a drop or an ask.

5. **Prove.** Spawn one prover per ask, in batches the machine's test runs can hold: a
   `delegate_task` child with `isolation: "worktree"`, in the Lifetime provers role. Its task gives
   the claim only (where, the sequence, what goes wrong, the backstop) and reads: "Read
   `~/.agents/workflow/skills/lifetime-audit/PROVE.md` and follow it."

   A `rejected` claim goes once to a fresh prover, with the first prover's reason and the
   instruction to try another sequence before rejecting; the second answer is final. A prover
   that ends without a verdict and left a test in its checkout: run that test yourself, without
   and then with its fix, and record that you did; one that left no test is spawned once more,
   fresh. A proof that changes the weighing (the hit turns out loud, or the backstop catches it)
   is weighed again as step 4 does: it becomes a drop only when it is now loud and unlikely.

   Done when every ask is `demonstrated`, `confirmed-by-reading` or finally `rejected`.

6. **Record and report.** Write the state file:
   `{"judged": [{"file": …, "blob": …, "commit": …, "bug": …, "shape": …}]}`, one entry per
   judged file, `blob` from `git rev-parse <commit>:<file>`, merged with the entries already
   there. Copy each prover's diff out of its checkout before T3 removes it. Reply with the report
   below: each proven ask in the plain words step 2 asks for (what breaks and for whom, how
   likely, what the fix costs) with your pick, and each drop as its line. An issue is filed only
   for an ask the user rules for, as step 2 says, carrying the prover's test and its failing
   output, or saying in its first line that it was confirmed by reading.

## Calibration

A run calibrates itself on what the project already knows:

- **Tracked bugs**: each bug a judge matched to a tracker issue shows the lifetime question finds
  real bugs here. A run that matches none while the tracker holds open lifetime bugs in the
  judged files has missed them: name those issues in the report.
- **Explicit lifecycles**: a judge whose slice holds one should return its Shape as `explicit`.

## Report

```
Lifetime audit: <repo> at <short sha>, <n> slices (<lines> lines), <a> asks proved, <d> drops

| Slice | Files | Bug | Shape | Proof |   (one row per slice)
## Asks          (proven, worst first: what breaks and for whom, how likely, the fix and its cost, your pick, the red assertion)
## Drops         (one line each: what it is, why it is unlikely, what the person sees)
## Tracked       (each bug a judge matched to an issue, with its number)
## Rejected      (each claim and the provers' reasons)
## Shapes worth fixing (the area and the sketch)
## Calibration   (tracked matches, missed tracked bugs, explicit lifecycles, unjudged slices)
```

Leave out an empty section.
