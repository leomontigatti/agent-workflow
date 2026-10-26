---
name: implement-spec
description: "Implement a PRD's sub-issues in parallel: background implementer children, one T3 worktree per ticket, merged onto this thread's branch and one draft PR, reviewed once at the end."
disable-model-invocation: true
---

# Implement a spec

The argument is a PRD issue number whose sub-issues `/to-tickets` filed. The goal is every
sub-issue built, merged onto this thread's branch, which is the **integration branch**, and one
PR that closes the chain, reviewed and babysat once.

The sub-issues are a **task graph**, not a list: their blocking edges decide what can start, and
the **frontier** is every open ticket whose blockers have all merged onto the integration branch.
Every ticket on the frontier runs at once, each in an implementer child with its own
worktree, except the first lone ticket (step 2). Talk to the implementers through pointers (the ticket, the PRD, the notes file, a
commit), never pasted summaries.

## 1. Read the graph

Start current, as `implement` step 1 says. Read the PRD with `gh issue view <PRD>` and
`--comments`, list its sub-issues with `gh issue view <PRD> --json subIssues`, and read each one
with `--json number,title,body,state,blockedBy`. A resumed run reads the PR body's
`## Sub-issues` checkboxes and the `Implemented in <sha>` comments to learn what already merged.

Two edges the tracker does not hold, added by you:

- **Migrations run one at a time.** Two tickets that each add a migration, or each bump the
  version a migration hangs on, would take the same number or fork the migration chain, so treat
  every pair of such tickets as blocked one on the other, in list order. A ticket whose text does
  not settle whether it touches the schema counts as one.
- **Shared names are fixed up front.** Worktrees postpone collisions to the merge. When two
  frontier tickets add to the same file, type, route or copy, either serialise them or fix the
  exact names in the notes file before spawning them.

Write the graph, those decisions and the names to `/tmp/implement-spec-<PRD>/notes.md`, outside
the repo, where every implementer can read it. Done when every ticket has its blockers listed.

If the PRD alters anything a user sees, capture its **before** now, from this worktree, as
`implement` step 1 says.

## 2. Run the frontier

Spawn one implementer per frontier ticket, all in one message: `delegate_task` with
`isolation: "worktree"`, `mode: "async"`, `role: "implementation"`, the `target` of the
Implementer row in `~/.agents/workflow/agents/models.md`, the ticket as `title`, and a
`clientRequestId` of `implement-spec-<PRD>-<n>-<attempt>`. T3 gives each child a prepared
checkout of this worktree's commit, with uncommitted edits left out. The task is pointers only:

```
Before anything else, read `~/.agents/workflow/agents/implementer.md` and follow it.

Ticket #<n>, part of PRD #<PRD>. Integration branch: <branch>.
Orchestrator worktree (not yours): <this worktree's path>.
Notes: /tmp/implement-spec-<PRD>/notes.md
```

Keep each `taskId` in the notes file, then end your turn: each child's completion wakes this
thread. This step needs `delegate_task`; outside a T3 thread, build every ticket yourself, one at
a time, as the lone ticket below.

An implementer pays for itself (a fresh read of the ticket and the code, a worktree and its
setup) through **parallelism** or a **fresh context**. A frontier of one ticket, with no
implementer running, offers no parallelism: build it yourself, by the implementer's step 2,
committing to the integration branch, then do step 3's comment, push and frontier recomputation
below (its items 2, 3 and 5). That holds once per session, a resumed one included:
send every later lone ticket to an implementer, whose fresh context keeps this session's short.

## 3. Merge each report

For each child's report (its result's `summary`) with `status: done`:

1. Check the branch builds on the tip: `git merge --ff-only <its branch>` in this worktree. When
   it is not a fast-forward (another ticket merged meanwhile), send the ticket back: a new child as
   in step 2, its task adding `Earlier branch: <its branch>`, and move on.
2. Comment `Implemented in <sha>. Part of #<PRD>.` on the sub-issue, which stays open
   (`docs/agents/issue-tracker.md` § PRD workflow).
3. Push. After the first merge, open the PR as a **draft** with the PRD PR body of the `pr` skill
   (§ PRD PRs there), linked to the thread as the `implement` skill's
   [THREADS.md](../implement/THREADS.md) says; after that, tick the sub-issue's box in its body.
   The chain pays one review at the end instead of one per slice.
4. Remove the implementer's worktree and branch (`git worktree remove <path>`,
   `git branch -d <branch>`), and an earlier attempt's: the child's thread opens no PR, so T3's
   storage cleanup has no merge to remove them on.
5. Recompute the frontier from what has merged onto the integration branch, never from GitHub's
   `blockedBy`, which drops only when a blocker closes, at the end. Spawn, as in step 2, only
   the tickets on it that are not already running: keep the merged and running tickets in the
   notes file, so neither starts twice.

A `blocked` report carries a question: answer it from the PRD if it settles it and send the ticket
back as in step 1, with the answer in the task; otherwise bring it to the user, and keep the rest of the graph running.

## 4. Close out, once

When every ticket has merged:

1. Run `implement` step 3, the validation list, on the integration branch.
2. Run `implement` step 5's review over the whole chain, once, since the branch point. Paste the
   PRD and every sub-issue into the Spec axis's prompt. Reviewing earlier reads every unbuilt
   ticket as a finding.
3. Send every **fix** to one `implementer`, spawned as in step 2 with the findings in place of
   the ticket number. Land it with step 3's fast-forward, push and worktree removal; there is no
   sub-issue to comment on or tick. Then re-run only the checks the findings named and step 5's
   fix round over the fixes: no second broad review.
4. Run `implement` step 4 now that the code is final, then step 7's screen approval: the user
   approves the **after** in the thread before the PR leaves draft.
5. Add the `## Review` record to the PR body (the `pr` skill), then
   `gh pr ready <n>`, then call the Skill tool with "babysit-pr".
6. Remove any implementer worktree still listed in `git worktree list`, and
   `/tmp/implement-spec-<PRD>/`.
