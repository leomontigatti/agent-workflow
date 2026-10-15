---
name: housekeeping
description: "Clean up what finished threads leave on this machine that T3's storage cleanup does not: local branches, per-worktree resources, and worktrees T3 did not create. Use when asked for housekeeping, a cleanup, or which worktrees or branches can be removed."
---

# Housekeeping

T3 Code's storage cleanup removes the worktrees T3 created, those in its managed folder
(`~/.t3/worktrees/<project>/`), once their PR merges or their last thread is deleted, and keeps
one with uncommitted changes (Settings → Storage; its "Last run" report names each one kept and
why). It keeps their branches. This skill sweeps what it leaves:

- **local branches**: T3 keeps the branch of every worktree it removes, so a resumed thread can
  recreate the checkout;
- **unmanaged worktrees**: one outside T3's folder, such as an implementer's under
  `.claude/worktrees/` that `implement-spec` did not remove, or one made by hand;
- **stack layers**: a worktree whose PR merged into another PR's branch rather than the default
  branch, which T3 does not count as merged;
- **the project's per-worktree resources**, when `docs/agents/housekeeping.md` exists: it names
  them (a database, a cache) and how to list and remove them. When it names a sweep command
  instead, run that command for steps 1 and 2 and report its output in step 1's shape.

Nothing is removed until the user accepts a dry-run report: a worktree that looks finished can
still be a paused thread.

1. **Survey, changing nothing.** `git worktree prune`, then `git worktree list --porcelain` gives
   each worktree's path and branch, and `git branch --format='%(refname:short) %(worktreepath)'`
   the branches with no worktree. For each, `git status --porcelain` in its worktree and
   `git rev-list --count origin/<default branch>..<branch>` show uncommitted work and unmerged
   commits, and `gh pr list --head <branch> --state all --json number,state,baseRefName` shows
   its PR. Report, with the reason for each:
   - **Would remove**: worktrees outside T3's folder whose PR is merged or closed and whose tree
     is clean, branches no worktree holds whose PR is merged or closed or that have no commits of
     their own, and the per-worktree resources of every worktree that is gone.
   - **Left to T3**: the worktrees in T3's folder, as a count. T3 never removes one whose branch
     was renamed or whose thread is archived; name those, since only the user frees them, by
     hand or in T3.
   - **Kept**: uncommitted changes, unpushed commits, an open PR, or the main checkout. Name every
     never-committed worktree too: a paused thread with no shell open looks exactly like a
     finished one, so those are where the user's eye is needed.

   Then stop. A request only to see what could be removed ends here.

2. **On acceptance**, remove only what the report listed, skipping any entry the user spared:
   `git worktree remove <path>` (never `--force`: it refuses a dirty tree, which is the point),
   then `git branch -d <branch>` (never `-D` unless the user said the commits are not needed; a
   branch git refuses to delete was not merged, so it is kept and reported). Remove each listed
   resource by name, as `docs/agents/housekeeping.md` says, never by a command that removes
   whatever is orphaned when it runs: that would take what became orphaned after the report.
   `git worktree prune` at the end.

3. Report what was removed as counts, anything an error stopped, and every kept worktree or
   branch with its reason. A kept one is the user's call: name it and leave it.
