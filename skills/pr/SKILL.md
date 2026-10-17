---
name: pr
description: "Write a PR body. Use when opening a PR or rewriting its description."
---

# PR body

PRs are squash-merged: the title becomes the commit subject, and the issue is the record of why.
The title is a Conventional Commit subject (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`,
`test:`, with a scope when one module owns the change) in English; when
`docs/agents/pull-requests.md` names a command that checks it, run it before `gh pr create`.

The body has two readers: the `review-record` check, which reads `## Review`, and the user, who
opens a PR only now and then, and never to approve it: screens are approved in the thread before
the PR opens (the `implement` skill's step 7), and the agent merges a PR whose merge is its own
(the `babysit-pr` skill). Write it in this template and stop:

```markdown
<anything the user must do or decide, first; omit when there is nothing>

<what changed, as the user or the maintainer would see it, in one to three sentences>

**Door: one-way.** <what a revert does not undo; the whole line only for a one-way door>

## Review

Tier: <tier>, reviewed <short sha>

- <axis> (<model>): <findings, fixed, declined>

Closes #N
```

## Rules

- **The issue carries the why.** The investigation, the alternatives and the domain reasoning live
  in the issue or an ADR; link them.
- **Anything the user must do or decide goes first**: a migration to run, a setting to change, a
  call that is theirs.
- **One concern per PR.** If the description needs the word "also", it is two PRs. A PRD PR is
  the deliberate exception (below).
- **`Closes #N`** closes the issue on merge (`docs/agents/issue-tracker.md` § Closing an issue).
- Write in the code language `AGENTS.md` sets; the user's language only inside backticks, as
  data, or where a term is the one a user reads. Use the domain's terms from `GLOSSARY.md`.
- The PR carries no screenshots or recordings: they were shown and approved in the thread.

## Door

A **one-way door** is a change a revert does not take back: something survives it. Its line keeps
the merge with the user (the `babysit-pr` skill), so a doubtful call is one-way: the session that
wrote the change is the one grading it. These are always one-way, however small the diff:

- A migration that drops or rewrites data: the contract step of an expand–contract change (the
  old column, table or form removed once nothing uses it), a backfill that overwrites, or
  anything the previous release cannot run against during a deploy. The expand step is two-way.
- Anything that reaches outside the system: a message or an email sent, a document submitted to
  another party, a file someone downloads. A revert does not unsend it.
- Production infrastructure: the hosting, DNS, secrets, a storage volume.
- Deleting data or files anywhere outside a test database.
- Every entry in `docs/agents/review.md` § One-way doors.

## Review

The record of `implement` step 5, which the `review-record` check reads. The first line is the
tier, as `review.py tier` printed it or raised, and the **reviewed commit**: the commit the last
review round covered. Then one line per reviewer: its axis (`readback`, `standards`, `spec`,
`correctness`) and model (`Sol`, `Opus`, `Luna`, `Sonnet`):

```markdown
## Review

Tier: full, reviewed 1a2b3c4

- standards (Sol): 1 finding, fixed
- spec (Sol): no findings
- correctness (Opus): 2 findings, 1 fixed, 1 declined
```

- Count every finding, the fix rounds' included. With two correctness reviewers, name how many
  each also found of the other's: that overlap is what the two-family trial measures.
- An axis that could not run says `skipped, <why>`; a role on its same-family fallback says so.
- A commit pushed later that changes more than docs or agent configuration fails the check until
  its own review round runs and the record names the new commit. A merge from the base does not
  count.

## PRD PRs

One PR carries every sub-issue of a PRD. Its body is one paragraph saying what the PRD delivers,
then `## Sub-issues` listing every sub-issue as a checkbox that carries its own keyword
(`- [ ] Closes #N <title>`), then the `Door: one-way` line when any slice is one, then `## Review` once the
chain has been reviewed, then `Closes #<PRD>`. GitHub closes only the
numbers that follow a closing keyword, and closing a parent does not close its sub-issues: a bare
`- [x] #N` stays open after the merge. The PRD holds the rest.

The session ticks each box when its slice lands on the branch, so the body is the progress record:
a session that resumes the PR reads it there, not in the scrollback, and nothing is committed to
the repository to track it.

## Stacked PRs

A change too big for one review ships as a stack: each layer a PR whose base is the layer below,
the bottom one on the default branch. Link the chain, bottom to top, with the `gh stack`
extension (`gh stack link <pr> <pr> ...`), so CI evaluates every layer as if it targeted the
default branch and its checks count. Each layer's body is written as above, for that layer
alone, with one line on top naming its place (`Layer 2 of 3, on #<n>`).

- **Merge** a stack with `gh stack merge <stack> --squash`, bottom up, in one operation. It
  refuses unless every layer is green and the stack is linear.
- **Linearity** breaks when the base moves or a lower layer gets a commit after the layer above
  branched. `gh stack rebase` and `gh stack push` restore it; the push force-pushes every rebased
  branch, so it waits for the user's sign-off. Never merge a branch into a layer by hand: a merge
  commit breaks linearity too.
- **Deleting a branch** that another open PR uses as its base closes that PR: delete only a leaf.
