---
name: test-audit
description: "Audit the tests a project gained since the last audit and open a PR that deletes the low-signal ones."
disable-model-invocation: true
---

A suite grows one reasonable test at a time, and most of the growth is tests that cannot name the
bug they catch. This audit reads only the tests added or grown since the last audit, judges each
against the test rules, and opens one PR that deletes or folds the **low-signal** ones. The user's
merge is the verdict: a test the user wants kept is restored on the PR, or the PR is closed.

It runs in a fresh thread on the project, in its own worktree from the default branch. It reads
the whole window and edits only test files.

## The rules

A test is judged by the bar the project already holds new tests to:

- `~/.agents/workflow/skills/tdd/SKILL.md`: § Anti-patterns, the "Name the bug first" rule and
  § Keeping the suite lean;
- the coding standards and test notes `AGENTS.md` routes to, which win where they differ.

A test is **kept** when you can name the bug it catches: the wrong implementation that makes it
fail. A test named for a real bug stays whatever its assertion looks like. A test is **protected**
when it covers an area in `docs/agents/review.md` § Full review or § Always ask: the audit never
edits a protected test, and lists a low-signal one as an ask.

## Steps

1. **Window.** The watermark is the default-branch commit the last audit reached, in
   `~/.local/state/test-audit/<repo>.json` (`{"reviewed": "<sha>"}`, `<repo>` the GitHub
   `owner-name`). With no file, start at the default-branch commit of seven days ago
   (`git rev-list -1 --before="7 days ago" origin/<default>`), or at the empty tree
   (`git hash-object -t tree /dev/null`) when the repo is younger than that. The window is
   `git diff <watermark> origin/<default>` over the test files, as the tests layout `AGENTS.md`
   routes to names them. The `origin/<default>` commit you diff against is the new watermark.
   - No test case added or grown → write the new watermark, reply with one line ("test audit:
     nothing new since <short sha>") and stop.

2. **Judge every case.** For each test case the window adds or grows, read it beside the code it
   exercises and the tests already near it, and give it one verdict:
   - **keep**: name the bug it catches in one line.
   - **delete**: name the anti-pattern or the rule it breaks, or the existing case that already
     catches its bug.
   - **fold**: its one new assertion belongs in an existing case; name that case.
   - **ask**: low-signal but protected, or a call only the user can make.

   Done when every case in the window carries a verdict and a reason.

3. **Apply.** On a `test/audit-<YYYY-MM-DD>` branch, make every delete and fold, and remove a
   fixture, helper or import only the deleted tests used. Run `docs/agents/validation.md`
   § Before committing until clean; a case whose removal breaks it is a keep after all, so restore
   it and move its verdict.
   - Nothing to delete or fold → write the new watermark, reply with the report from step 5 and
     open no PR.

4. **Review.** Commit as `test: delete <n> low-signal tests added since <short sha>`, then review
   the branch as step 5 of `~/.agents/workflow/skills/implement/SKILL.md` says, tier and fix
   round included. The spec any axis asks for is this skill and the step 2 verdicts. A
   reviewer's finding that a deleted case does catch a bug restores it as a keep. Commit each
   round's fixes before the next step, so the reviewed commit is the branch's head.

5. **Report and open the PR.** Push, and open the PR ready for review, with a body written by
   calling the Skill tool with "pr" (its `## Review` record included) and holding:

   ```
   Window: <watermark short sha>..<new short sha>, <n> cases judged

   ## Asks       (protected or user's call: file, test, reason, your pick)
   ## Deleted    (file, test, reason)
   ## Folded     (file, test, the case it went into)
   ## Kept       (count, and one line per kept case only when the bug it names is not obvious from its title)
   ```

   Leave out an empty section. Then write the new watermark. Merging is the user's: link the PR
   to the thread and leave it there, without a babysit.

## Cadence

Weekly: a T3 scheduled task per project, "Weekly test audit", on Mondays at 10:00, in a fresh
thread on that project. A missed week leaves the watermark where it was, so the next run covers
both. A run's thread is its record: a thread with no report is a failed run, whatever the task's
`lastRunStatus` says.
