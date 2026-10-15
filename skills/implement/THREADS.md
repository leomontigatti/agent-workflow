# Branches, worktrees and T3 Code threads

The rules every shared skill assumes about where a session works. Local sessions run inside T3
Code, and every thread gets its own git worktree and branch: `t3.json` sets
`defaultThreadEnvMode` to `worktree`, and its `runOnWorktreeCreate` script prepares the worktree
before the agent starts. The main checkout stays on the default branch and is nobody's working
directory.

- **Work where you started.** The thread's worktree is the working directory. Never `git checkout`
  or `git switch` in the main checkout, and never create a worktree of your own (`git worktree
  add`, Claude's `EnterWorktree`): T3 tracks only the branch and PR of the worktree it created,
  so a private worktree loses the PR badge, the settling of the thread and T3's storage cleanup. A
  session that needs another checkout gets it from T3 (`t3_thread_launch` with a
  `workspaceStrategy`). The one exception is `implement-spec`'s implementer subagents, each in an
  Agent-tool worktree under `.claude/worktrees/`: their branches merge into the thread's, which
  keeps the PR, and the skill removes them.
- **Branch names.** T3 names the branch when it creates the thread and may rename it once the
  thread starts, so read it with `git branch --show-current`, never from the worktree's folder
  name. A session that renames it or creates one uses `feat/`, `fix/`, `docs/`, `chore/`,
  `refactor/`, `research/` or `prototype/`.
- **One thread, one branch, one PR.** After `gh pr create`, register the PR with the thread
  through the `link_pull_request` tool, so T3 shows its status and settles the thread when it
  merges. To keep working on an existing PR, start the thread on that branch (or link the PR)
  instead of checking it out in another worktree.
- **A launched thread reports to its own inbox.** A thread started with `t3_thread_launch`
  babysits its own PR and hands back to the user; its `unwatch_pull_request` wakes nobody else, so
  the launcher never hears that the PR is ready. When the user hands the merge to the launcher,
  the child still babysits and the launcher owns only the wait: `list_thread_pull_requests` with
  the child's `threadId` gives the child's PR, the launcher calls `watch_pull_request` on it, and
  merges when its own read of the round (the `babysit-pr` state table) says READY. That list is
  the only source for a child PR's state. A launcher turn that ends before a child has opened its
  PR names that child in its report, since nothing will wake the launcher for it.
- **Read-only threads** (writing issues, triage, reviewing a PR without editing code) change no
  branch.
- **Leaving a worktree behind is fine; abandoning a branch is not.** Push the branch or delete it.
  T3's storage cleanup removes a worktree T3 created once its PR merges or its last thread is
  deleted, and keeps the branch; the branches, and the worktrees it skips, go with the
  `housekeeping` skill.
- **Investigate before implementing.** A request to investigate, review, diagnose, audit or
  explain is a request for findings: return them with the options, their trade-offs and a
  recommended next step, then wait. Editing starts when the user asks to implement, fix, apply or
  change something.
