# Branches, machines and threads

The rules every shared skill assumes about where a session works. A session is a Capy thread, and
every thread gets its own machine with its own clone of the project's repos, prepared by the
project's Setup before the agent starts. Nothing is shared between threads but what is pushed.

- **Check the machine first.** `ls ~/.agents/skills` lists the shared skills and
  `~/.agents/workflow` resolves. When either is missing the Setup did not run: stop and say so.
- **One thread, one branch, one PR.** Before the first edit, start current (`git fetch origin`,
  then branch from `origin/<default branch>`) on a branch named `feat/`, `fix/`, `docs/`,
  `chore/`, `refactor/`, `research/` or `prototype/`. Open the PR with the platform's PR tool,
  never `gh pr create`: the thread is then woken when its checks finish and when someone
  comments. To keep working on an existing PR, check out its branch in a new thread.
- **One writer per checkout.** A subagent shares this machine and this checkout: a subagent that
  judges reads there and writes nothing. A second writer is a thread of its own in the project,
  which gets its own machine and sees only what is pushed, so push before starting it and have
  it push before it reports.
- **A thread you start owns its PR.** It follows `babysit-pr` on it and hands back to the user;
  the thread that started it reads that PR's state from GitHub, never from the child's word.
- **A machine that slept kept its disk and lost its processes.** After a pause, restart what the
  task needs (a dev server, a watcher) before relying on it.
- **Merging is the user's.** Merge a PR, or turn on auto-merge, only when the user asks for that
  merge in this thread.
- **Issues live on GitHub**, as the project's `docs/agents/issue-tracker.md` says, not in the
  platform's own tracker.
- **Read-only threads** (writing issues, triage, reviewing a PR without editing code) change no
  branch.
- **Push the branch or delete it** before the thread ends: the machine is cleared after it has
  slept long enough, and an unpushed branch goes with it.
- **Investigate before implementing.** A request to investigate, review, diagnose, audit or
  explain is a request for findings: return them with the options, their trade-offs and a
  recommended next step, then wait. Editing starts when the user asks to implement, fix, apply or
  change something.
