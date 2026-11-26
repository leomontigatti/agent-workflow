# Branches, machines and threads

The rules every shared skill assumes about where a session works. A session is a Capy thread, and
every thread gets its own machine with its own clone of the project's repos, prepared by the
project's Setup. Nothing is shared between threads but what is pushed.

- **Check the machine first.** `ls ~/.agents/skills` lists the shared skills and
  `~/.agents/workflow` resolves. When either is missing the Setup did not run: stop and say so.
- **Make the checkout current before reading a project file.** A thread can start while the
  Setup is still running, and a file read then is the version the machine's snapshot held. At
  the thread's start, a read-only thread's included, run
  `git fetch origin && git log --oneline HEAD..@{upstream}`: the checkout is current when it
  prints nothing. When it prints commits, `git merge --ff-only @{upstream}`, then read again
  every project file already read. A subagent on this machine skips the check: its thread ran
  it. While a tool result says the Setup is still running, a command or file it installs may
  be missing: use it once the platform reports the Setup finished.
- **Read one file per call**, or a range of one: a result over about 20 KB comes back cut, and
  what is cut is its end.
- **One thread, one branch, one PR.** Before the first edit, start current (`git fetch origin`,
  then branch from `origin/<default branch>`) on a branch named `feat/`, `fix/`, `docs/`,
  `chore/`, `refactor/`, `research/` or `prototype/`. Open the PR with the platform's PR tool,
  never `gh pr create`: the thread is then woken when its checks finish, when someone in the
  organization reviews or comments, and, while a person has written in the thread lately (3 days by default, set per organization), when it merges or closes:
  a thread another agent started is not woken by its merge (the `babysit-pr` skill § 2). To keep working on an existing PR, check out its branch in a new thread.
- **One writer per checkout.** A subagent that judges shares this machine and this checkout,
  reads there and writes nothing. A second writer is a subagent on its own machine, which sees
  only what is pushed: push before starting it, and have it push before it reports.
- **Size a machine by its job.** A thread, or a subagent on its own machine, takes the project's
  size unless you name one, and every awake machine counts against one memory cap for the whole
  organization. Name the smallest that fits: **small** for work that reads and writes text (docs,
  ADRs, the glossary, issue triage, reading a PR), **medium** for a script or config change with
  a light test, the project's size for anything that runs its test suite, a build or a dev server.
  A thread that commits takes at least the size its project's commit hook runs in, when
  `docs/agents/validation.md` § Before committing names one.
  A role that only reads this checkout is a subagent on this machine, which adds nothing. A start refused for
  memory means the cap is reached: say what ran and what did not, and start the rest when a
  machine has gone to sleep.
- **A thread you start owns its PR.** It follows `babysit-pr` on it and hands back to the user;
  the thread that started it reads that PR's state from GitHub, never from the child's word.
- **A machine that slept kept its disk and lost its processes.** After a pause, restart what the
  task needs (a dev server, a watcher, a browser's sign-in) before relying on it.
- **A message carries at most 10 attachments.** Send more as several messages.
- **A message to a finished subagent resumes it**, even when the send returns `resumed: false`:
  wait for its report, and start no second subagent for the same work.
- **Merging is the user's**, or the repo's grant. Merge a PR only when the user asks for that
  merge in this thread, or when the repo's root `AGENTS.md` on its default branch grants the
  agent merges of that PR's kind in so many words (the `babysit-pr` skill). Turn on auto-merge
  only when the user asks. Nothing blocks a merge nobody asked for; this rule does.
- **Issues live where the project's `docs/agents/issue-tracker.md` puts them**, on GitHub or in
  the platform's own tracker: read and write them only the way that file says.
- **Read-only threads** (writing issues, triage, reviewing a PR without editing code) change no
  branch.
- **Push the branch or delete it** before the thread ends: the machine is cleared after it has
  slept long enough, and an unpushed branch goes with it.
- **Investigate before implementing.** A request to investigate, review, diagnose, audit or
  explain is a request for findings: return them with the options, their trade-offs and a
  recommended next step, then wait. Editing starts when the user asks to implement, fix, apply or
  change something.
