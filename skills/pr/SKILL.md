---
name: pr
description: "Write a PR body. Use when opening a PR or rewriting its description."
---

# PR body

PRs are squash-merged: the title becomes the commit subject, and the issue is the record of why.
The title is a Conventional Commit subject (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`,
`test:`, with a scope when one module owns the change) in English; when
`docs/agents/pull-requests.md` names a command that checks it, run it before `gh pr create`. The
body is for the reviewer, who has the diff open. Write it in this template and stop:

```markdown
<anything the reviewer must do or decide, first; omit when there is nothing>

## Summary

<the problem in one or two sentences, then the fix: a short paragraph or a few bullets, and a
picture when the point is structure or order>

## Evidence

- **Before:** <screenshot / failing test run / output>
  **After:** <screenshot / passing test run / output>

## Merge Danger

**Door:** <one-way or two-way>

<optional: what a revert does not undo>

**Blast Radius:** <one or two words>

<optional: what breaks, and for whom, if the change is wrong>

## Review

Tier: <tier>, reviewed <short sha>

- <axis> (<model>): <findings, fixed, declined>

Closes #N
```

## Rules

- **Do not restate the issue.** The investigation, the alternatives and the domain reasoning live
  in the issue or an ADR. Link them; a reviewer who wants them follows the link.
- **Anything the reviewer must do or decide goes first**, above `## Summary`: a migration to run,
  a setting to change, a call that is theirs.
- **One concern per PR.** If the description needs the word "also", it is two PRs. A PRD PR is
  the deliberate exception (below).
- **`Closes #N`** closes the issue on merge (`docs/agents/issue-tracker.md` § Closing an issue).
- Write in the code language `AGENTS.md` sets; the user's language only inside backticks, as
  data, or where a term is the one a user reads. Use the domain's terms from `GLOSSARY.md`.
- Skip preambles and keep prose brief. Name a symbol or a file only when the reviewer would not
  find it alone.

## Summary

Say what was wrong or missing, as the user or the maintainer would see it, then what changed and,
when it is not obvious from the diff, why this way. A bullet that runs past three lines is a sign
that a picture would have been shorter.

A picture here is a small text drawing in a fenced block, chosen by what the reader has to see:

| The point is…                          | Draw                                                        |
| -------------------------------------- | ----------------------------------------------------------- |
| a decision the code makes, step by step | indented pseudocode, one branch per line                    |
| who calls whom, in what order          | an indented call list, callers above callees                |
| how a screen is built                  | the component nesting, with the state each part owns        |
| where things now live                  | a two-level directory sketch, one comment per entry         |
| messages between parts over time       | a Mermaid `sequenceDiagram`                                 |
| a small change to an existing shape    | a `diff` block of the shape, not of the code                |

For example, a fix to when a cache is used:

```text
save(note)
  unchanged since last save? → return the stored result
  otherwise                  → write, then refresh the stored result
```

Draw only the calls, files, fields and states the point depends on, put the picture beside the
sentence it supports, and use one, two at most. Paste a whole block instead only when most of it
is new or the reviewer needs to copy it.

## Evidence

Concrete evidence that the change works, as a before and after, captured as
`docs/agents/verification.md` § Evidence says.

- **What a user sees** is shown, not described: a change to a screen carries before and after
  images, a change to motion or interaction a short recording, a change to a printed or exported
  document its before and after output. Capture against test data, never real people's.
- **A test** is the next best: name it and say it failed without the change, with the failing
  output. A list of green commands is a claim, not a before and after.
- Say what was checked by hand, and what was not. Never claim a command that was not run; if
  nothing beyond CI was, say so in one line instead of the before/after pair.

## Merge Danger

**Door** says whether a revert takes the merge back (**two-way**) or something survives it
(**one-way**). It tells the reviewer how slowly to read. These are always one-way doors, however
small the diff:

- A migration that drops or rewrites data: the contract step of an expand–contract change (the
  old column, table or form removed once nothing uses it), a backfill that overwrites, or
  anything the previous release cannot run against during a deploy. The expand step is two-way.
- Anything that reaches outside the system: a message or an email sent, a document submitted to
  another party, a file someone downloads. A revert does not unsend it.
- Production infrastructure: the hosting, DNS, secrets, a storage volume.
- Deleting data or files anywhere outside a test database.
- Every entry in `docs/agents/review.md` § One-way doors.

The session that wrote the change is the one grading it, so a doubtful call is one-way. A one-way
door the reviewer has to act on also goes first, above `## Summary`.

**Blast Radius** is what breaks, and for whom, if the change is wrong: one screen for one role,
every customer's invoices, a nightly job. Consider all of it: layout shift, mobile, other callers
of a changed module, consumers of a changed doc.

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
(`- [ ] Closes #N <title>`), then `## Merge Danger` for the whole chain, then `## Review` once the
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

## Example

```markdown
## Summary

Clearing the search box while a search was still loading kept the old results.

- The table compared the next query against the current location, which lags a navigation in
  flight; it now reads the query the pending navigation is heading to.

## Evidence

- **Before:** `clears while a search is still loading` fails: the delayed load keeps the old query.
  **After:** it passes.
- Not clicked through in a browser.

## Merge Danger

**Door:** two-way

**Blast Radius:** table search

Closes #N
```
