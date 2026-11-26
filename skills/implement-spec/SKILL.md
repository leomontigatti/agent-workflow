---
name: implement-spec
description: "Implement a PRD's sub-issues in parallel: implementer subagents, one machine per ticket, merged onto this thread's branch and one draft PR, reviewed once at the end."
disable-model-invocation: true
---

# Implement a spec

The argument is a PRD issue number whose sub-issues `/to-tickets` filed. The goal is every
sub-issue built, merged onto this thread's branch, which is the **integration branch**, and one
PR that closes the chain, reviewed and babysat once.

The sub-issues are a **task graph**, not a list: their blocking edges decide what can start, and
the **frontier** is every open ticket whose blockers have all merged onto the integration branch.
Every ticket on the frontier runs at once, each in an implementer subagent on its own
machine, except the first lone ticket (step 2). Talk to the implementers through pointers (the ticket, the PRD, the build notes, a
commit), never pasted summaries.

## 1. Read the graph

Start current, as `implement` step 1 says. Read the PRD's body and its comments, list
its sub-issues, and read each one's body with its state and its open blockers, the way
`docs/agents/issue-tracker.md` gives each of those reads. Where that file gives the
mark of an issue a session has started, and of one whose PR is open, the PRD takes the first now
and each sub-issue the second when step 3 lands it. A resumed run reads the PR body's
`## Sub-issues` checkboxes and the `Implemented in <sha>` comments to learn what already merged,
and, once the PR is open, gives each landed sub-issue the mark it lacks.

Two edges the tracker does not hold, added by you:

- **Migrations run one at a time.** Two tickets that each add a migration, or each bump the
  version a migration hangs on, would take the same number or fork the migration chain, so treat
  every pair of such tickets as blocked one on the other, in list order. A ticket whose text does
  not settle whether it touches the schema counts as one.
- **Shared names are fixed up front.** Separate machines postpone collisions to the merge. When
  two frontier tickets add to the same file, type, route or copy, either serialise them or fix
  the exact names in the build notes before starting them.

An implementer has nobody to pick a design, so **every ticket the prototype gate of
`implement` step 1 catches has its winner before it runs**: its `## Design` section, or a winner
comment on the PRD for its screen. When one has neither, run the prototype pass for those screens
now, as `to-spec` step 4 says, and stop for the user's pick; the frontier waits for it.

Write the graph, those decisions and the names as the **build notes**: one comment on the PRD
opening `## Build notes`, edited in place from then on, since an implementer's machine sees
only the tracker and what is pushed. Keep what only you need (which subagent runs which ticket, each attempt's branch)
in `~/.capy/work/implement-spec-<PRD>/state.md`, which a wake does not clear. Done when every ticket has its blockers listed.

If the PRD alters anything a user sees, its reference comes as `implement` step 1 says: the
approved variants of the PRD's prototype pass (`to-spec`), or a **before** captured now, from this
checkout.

## 2. Run the frontier

Push the integration branch, then start one implementer per frontier ticket, all at once: a
subagent on its own machine with a clean checkout, on the model and effort of the Implementer row
in `~/.agents/workflow/agents/models.md`, titled with the ticket. Count them first, as that
file's fan-out rule says. The task is pointers only:

```
Before anything else, read `~/.agents/workflow/agents/implementer.md` and follow it.

Ticket <ticket>, part of PRD <PRD>. Integration branch: <branch>.
Your branch: <branch>-t<n> (a later attempt: <branch>-t<n>-a<attempt>).
```

`<ticket>` and `<PRD>` are written as the tracker writes them (`#12`, `ABC-12`), and `<n>` is the
ticket's number alone.

Note each attempt's subagent and branch in the state file, then end your turn: each report wakes
this thread.

An implementer pays for itself (a fresh read of the ticket and the code, a machine and its
setup) through **parallelism** or a **fresh context**. A frontier of one ticket, with no
implementer running, offers no parallelism: build it yourself, by the implementer's step 2,
committing to the integration branch, then do step 3's comment, push and frontier recomputation
below (its items 2, 3 and 5). That holds once per session, a resumed one included:
send every later lone ticket to an implementer, whose fresh context keeps this session's short.
Send the first one too when it sweeps the codebase (a rename, a removed concept, a change its
text spreads over many files): reading it here would fill this session before the graph has run.

## 3. Merge each report

For each implementer's report with `status: done`, unless the state file marks
its ticket retired (a report that crossed § Route change: discard its branch as that section does):

1. Check the branch builds on the tip: `git fetch origin <its branch>`, then
   `git merge --ff-only origin/<its branch>` here. When it is not a fast-forward (another ticket
   merged meanwhile), message the implementer that built it to fetch, merge
   `origin/<integration branch>` into its branch, rerun its checks, push and report again, and
   move on. Only when it cannot be resumed, send the ticket to a new implementer as in step 2,
   its task adding `Earlier branch: <its branch>`.
2. Comment `Implemented in <sha>. Part of <PRD>.` on the sub-issue, which stays open
   (`docs/agents/issue-tracker.md` § PRD workflow). Every comment this skill posts on GitHub
   opens with the agent note of the `pr` skill § Rules; one posted in another tracker follows
   that tracker's doc.
3. Push. After the first merge, open the PR as a **draft** with the PRD PR body of the `pr` skill
   (§ PRD PRs there), with the platform's PR tool as the `implement` skill's
   [THREADS.md](../implement/THREADS.md) says; after that, tick the sub-issue's box in its body.
   The chain pays one review at the end instead of one per slice.
4. Delete the implementer's branch on the remote (`git push origin --delete <branch>`), and
   every earlier attempt's: no PR will ever merge them.
5. Recompute the frontier from what has merged onto the integration branch, never from the
   tracker's blocking relation, which clears only when a blocker closes, at the end. Spawn, as in step 2, only
   the tickets on it that are not already running: keep the merged and running tickets in the
   state file, so neither starts twice.

A `blocked` report carries a question: when the PRD settles it, message the answer to the
implementer that asked, which resumes with what it has read, or to a new one as step 1 does when
it cannot be resumed; otherwise bring it to the user, and keep the rest of the graph running.

## Route change

When a decision is replaced mid-build (a `blocked` question's answer, or the user's call) and the
destination stays the same, the spec gets its `## Changed during the build` line (`to-spec`
§ A snapshot, not a source) and the graph changes with it:

1. **Retire** each unmerged ticket the change replaces: stop its running subagent, delete its
   branch and every earlier attempt's on the remote (`git push origin --delete <branch>`), mark
   it retired in the state file, and close it as
   `docs/agents/issue-tracker.md` § Closing an issue says for work that will not be done. A
   ticket already merged is not retired: what the change undoes in it is a new ticket in item 2.
   Before deleting, check the target: a branch named `<integration branch>-t<n>…`, never the
   integration branch itself.
2. **Replace** it: draft the new tickets with the user as `to-tickets` does (its § 4 quiz, then
   § 5's publishing as sub-issues of the PRD). Comment the replacement's number on each retired
   ticket, and in the PR body's `## Sub-issues` strike each retired line
   (`- [x] ~~<ticket> <title>~~ replaced by <its replacement>`) and add each new ticket.
3. **Re-point the edges**: every open ticket a retired one blocked is now blocked by that
   ticket's replacements, in the tracker (`docs/agents/issue-tracker.md` § Ticket operations) and
   in the build notes, so nothing waits on a retired ticket or respawns it.
4. Recompute the frontier as step 3 item 5 does.

## 4. Close out, once

When every ticket that is not retired has merged:

1. Run `implement` step 3, the validation list, on the integration branch.
2. Run `implement` step 5's review over the whole chain, once, since the branch point. Paste the
   PRD and every sub-issue that is not retired into the Spec axis's prompt. Reviewing earlier reads every unbuilt
   ticket as a finding.
3. Send every **fix** to one `implementer`, spawned as in step 2 with the findings in place of
   the ticket number. Land it with step 3's fast-forward, push and branch removal; there is no
   sub-issue to comment on or tick. Then re-run only the checks the findings named and step 5's
   fix round over the fixes: no second broad review.
4. Run `implement` step 4 now that the code is final, then step 7's screen approval: an **after**
   that matches its approved variant is shown and stands, and any other is approved by the user in
   the thread before the PR leaves draft.
5. Add the `## Review` record to the PR body (the `pr` skill), then `gh pr ready <n>`, then push
   one empty commit: a PR marked ready on the commit it was drafted on reports `BLOCKED` with every
   required check green until a new commit lands, and the reviewed commit in the record stands.
   Then follow the `babysit-pr` skill: where the tracker closes a built issue by hand, its
   step 5 closes the PRD and every sub-issue after the merge.
6. Delete any implementer branch still on the remote (`git ls-remote --heads origin
   '<integration branch>-t*'`).
