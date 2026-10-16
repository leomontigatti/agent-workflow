---
name: housekeeping
description: "Clean up what finished threads leave on this machine that T3's storage cleanup does not: local branches, per-worktree resources, and the worktrees T3 skips. Use when asked for housekeeping, a cleanup, or which worktrees or branches can be removed."
---

# Housekeeping

T3 Code's storage cleanup is the first line: it removes a worktree in its managed folder
(`~/.t3/worktrees/<project>/`) on the rules set in Settings → Storage, hourly, and its "Last run"
report names each worktree it kept and why. This skill hands T3 everything T3 can do, and sweeps
only what T3 leaves by design:

| Left behind                                   | Why T3 leaves it                                                    | Who cleans it                    |
| --------------------------------------------- | ------------------------------------------------------------------- | -------------------------------- |
| a merged or deleted thread's worktree         | nothing: T3 removes it (`worktreeOnMerge`, `worktreeOnDelete`)      | T3                               |
| the local branch of every worktree T3 removed | kept on purpose, so a resumed thread can recreate its checkout      | this sweep                       |
| worktrees outside T3's folder (`.claude/worktrees/`, hand-made) | never T3's                                         | this sweep                       |
| a worktree whose branch was renamed           | T3 keeps it as "repository or branch changed"                       | this sweep, until T3 fixes it    |
| an archived thread's worktree                 | T3's sweep skips archived threads                                   | this sweep, until T3 fixes it    |
| a stack layer merged into another PR's branch | T3 counts only merges into the default branch                       | this sweep, until T3 fixes it    |
| a folder in T3's folder that no thread uses   | T3 lists it under Last run but never removes it                     | this sweep, until T3 fixes it    |
| per-worktree resources (a database, a cache)  | T3 runs no script when it removes a worktree                        | this sweep, by `docs/agents/housekeeping.md` |

The "until T3 fixes it" rows are watched in the shared `t3-dependencies.md`; when one is fixed,
its row moves to T3 here.

Nothing is removed until the user accepts a dry-run report: a worktree that looks finished can
still be a paused thread.

1. **Check T3's rules, changing nothing.** Read the `storageCleanup` block of T3's settings
   (`~/.t3/userdata/settings.json`). `worktreeOnMerge` and `worktreeOnDelete` must be on; report
   either one off as the first thing the user can fix, since T3 then leaves work this sweep is not
   built for. `worktreeSettledAfterDays` on is welcome: it hands T3 the settled threads whose PR
   never merged; when it is off, say so once, as an option. Report `worktreeAfterDays` or
   `worktreeUnchanged` on as a risk: T3 then removes a live thread's worktree and recreates it on
   resume, and this sweep would take the recreated one's resources for orphans.

2. **Survey, changing nothing.** `git worktree prune`, then `git worktree list --porcelain` gives
   each worktree's path and branch, and `git branch --format='%(refname:short) %(worktreepath)'`
   the branches with no worktree. For each, `git status --porcelain` in its worktree and
   `git rev-list --count origin/<default branch>..<branch>` show uncommitted work and unmerged
   commits, and `gh pr list --head <branch> --state all --json number,state,baseRefName` shows
   its PR. `t3_worktree_list` tells which worktrees T3 tracks and their threads; a folder in
   T3's folder it does not list is an orphan, judged by the same checks. When
   `docs/agents/housekeeping.md` exists, it says how to list the project's per-worktree resources,
   or names a sweep command that replaces this step and the next. Report, with the reason for
   each:
   - **Would remove**: branches no worktree holds whose PR is merged or closed, or that have no
     commits of their own; worktrees from the table's "this sweep" rows whose PR is merged or
     closed and whose tree is clean; and the resources of every worktree that is gone.
   - **Left to T3**: the worktrees in T3's folder that its rules will remove, as a count. When its
     Last run says it kept one for an open terminal or a running thread, name the thread.
   - **Kept**: uncommitted changes, unpushed commits, an open PR, or the main checkout. Name every
     never-committed worktree too: a paused thread with no shell open looks exactly like a
     finished one, so those are where the user's eye is needed.

   Then stop. A request only to see what could be removed ends here.

3. **On acceptance**, remove only what the report listed, skipping any entry the user spared:
   `git worktree remove <path>` (never `--force`: it refuses a dirty tree, which is the point),
   then `git branch -d <branch>` (never `-D` unless the user said the commits are not needed; a
   branch git refuses to delete was not merged, so it is kept and reported). Remove each listed
   resource by name, as `docs/agents/housekeeping.md` says, never by a command that removes
   whatever is orphaned when it runs: that would take what became orphaned after the report.
   `git worktree prune` at the end.

4. Report what was removed as counts, anything an error stopped, and every kept worktree or
   branch with its reason. A kept one is the user's call: name it and leave it.
