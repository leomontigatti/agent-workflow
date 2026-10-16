# T3 Code dependencies: shared workflow

What the shared skills, agents and hooks in this repo assume about T3 Code. The
`t3-update-review` skill reads this file after every T3 update, beside each project's own
`docs/agents/t3-dependencies.md`, which records only what that project assumes beyond this file.
Agents don't need it for everyday work.

Status of an entry:

- **active**: we rely on T3 behaving this way; an update that changes it breaks us.
- **watching**: a workaround for something T3 can't do (yet), or a workflow T3 could do natively
  better, faster or cheaper. "Would improve if" is the exact condition that lets us simplify.
- **ready**: the condition is met in the installed T3, but we haven't adopted it yet.
- **resolved**: adopted; kept as history.

T3 source paths below are in pingdotgg/t3code.

## Active

### worktree-per-thread

- **Relies on:** a project's `t3.json` sets `defaultThreadEnvMode` to `worktree`, and its
  `runOnWorktreeCreate` script with `async: false` runs in each new thread worktree and holds the
  agent until it exits. The script gets `T3CODE_PROJECT_ROOT`, and `T3CODE_WORKTREE_PATH` for a
  worktree (`packages/contracts/src/t3ProjectFile.ts`, `packages/shared/src/projectScripts.ts`).
  T3 runs the script only once the project imported `t3.json` (project settings → Actions →
  Import from t3.json).
- **Used by:** `skills/implement/THREADS.md`; `agents/implementer.md` step 2 (runs the same
  script by hand, with `T3CODE_PROJECT_ROOT` set, for a worktree T3 did not create)
- **Breaks if:** T3 stops applying `defaultThreadEnvMode` or running create-time scripts, starts
  the agent before an `async: false` script exits, or stops passing `T3CODE_PROJECT_ROOT`.

### own-worktrees-only

- **Relies on:** T3 tracks the branch and PR of the worktree it created for a thread, and leaves
  any worktree outside its managed folder alone: it neither sets one up nor removes it ("outside
  the managed worktree folder" in `apps/server/src/storageCleanup.ts`).
- **Used by:** `skills/implement/THREADS.md` ("Work where you started");
  `skills/implement-spec/SKILL.md` § 2, § 3 step 4 and § 4 step 6;
  `skills/housekeeping/SKILL.md` (the worktrees the sweep owns)
- **Breaks if:** T3's cleanup starts removing worktrees outside its managed folder, which would
  race the removal `implement-spec` and `housekeeping` do themselves.

### storage-cleanup-removes-thread-worktrees

- **Relies on:** T3's storage cleanup is on (`storageCleanup` in `~/.t3/userdata/settings.json`:
  `worktreeOnMerge: true`, `worktreeOnDelete: true`; `worktreeKeepWhen` left at its default,
  `uncommitted-changes`). Hourly, at startup and on a settings change, it removes a worktree in
  its managed folder (`~/.t3/worktrees/<project>/`) once the thread's PR merges into the default
  branch or its last thread is deleted (archived ones included), keeps one with uncommitted
  changes, an open terminal, a running or queued thread or an open provider session, and reports
  why it kept each one under Settings → Storage → Last run. A worktree other threads share is
  kept, unless every one of them is a subagent of the same parent, whose rules then decide
  (pingdotgg/t3code#19748, since 0.1.1-nightly.20261016.3203): that is what lets a thread whose
  reviewers ran through `delegate_task` in its checkout be removed. Last run also lists folders
  in the managed folder no thread uses (pingdotgg/t3code#19749), which T3 never removes. It keeps
  the branch on purpose, runs no script on removal, and has no MCP tool to trigger or read it
  (`apps/server/src/storageCleanup.ts`; `packages/contracts/src/settings.ts`;
  `docs/user/project-settings.md` § Storage cleanup).
- **Used by:** `skills/housekeeping/SKILL.md` (its table, and step 1 reads the settings);
  `skills/implement/THREADS.md` ("Leaving a worktree behind is fine")
- **Breaks if:** the settings are reset or the rules turned off; `worktreeAfterDays` or
  `worktreeUnchanged` is turned on, since T3 then removes a live thread's worktree and recreates
  it on resume; T3 moves its managed folder, so `housekeeping` would take T3's worktrees for its
  own; T3 again keeps every worktree a subagent shares, so each reviewed thread's worktree stays;
  or the Last run report moves or stops giving a reason.

### renamed-branch-in-thread

- **Relies on:** a thread keeps working after its worktree's branch is renamed with
  `git branch -m`, and a PR linked by URL or number keeps its status. The link carries no branch
  name (`PullRequestTargetInput` in `apps/server/src/mcp/toolkits/pullRequests/tools.ts`).
- **Used by:** `skills/implement/THREADS.md` ("Branch names")
- **Breaks if:** T3 starts resolving a thread's PR, or its state, from the branch name recorded
  when the thread started.

### pr-linked-by-tool

- **Relies on:** `link_pull_request` accepts a PR URL, or repository and number; a repeat call
  returns `alreadyLinked`; the linked PR's status shows beside the thread, and the thread settles
  when the PR merges (`apps/server/src/mcp/toolkits/pullRequests/tools.ts`).
- **Used by:** `skills/implement/THREADS.md` ("One thread, one branch, one PR");
  `skills/implement/SKILL.md` § 7; `skills/implement-spec/SKILL.md` § 3 step 3
- **Breaks if:** the tool is renamed or removed, stops taking a URL, or stops showing status or
  settling the thread on merge.

### pr-watch-is-native

- **Relies on:** `watch_pull_request` links the PR if needed, has T3 check it about every two
  minutes, and wakes the thread on a failed check, passed required checks, a new or edited
  comment or review, or a conflict with the base. Only comments posted after the call wake the
  thread. A subagent thread cannot call it. `unwatch_pull_request` ends the watch and returns the
  thread to the user's inbox; it wakes no other thread. `list_thread_pull_requests` with another
  thread's `threadId` lists that thread's PRs.
- **Used by:** `skills/babysit-pr/SKILL.md` § 2 and § 5; `skills/implement/SKILL.md` § 7;
  `skills/implement/THREADS.md` ("A launched thread reports to its own inbox")
- **Breaks if:** a wake event is dropped, or a wake no longer ends the turn, so the session has to
  poll or sleep to wait; `unwatch_pull_request` stops returning the thread to the inbox;
  `list_thread_pull_requests` stops taking another thread's id; or inactivity auto-settle is
  turned on without "Keep threads with a PR" (pingdotgg/t3code#14642), which settles a thread
  while it babysits and ends its watch.

### delegate-task-reviews

- **Relies on:** `delegate_task` takes `task`, `target` (`providerInstanceId`, `model`,
  `options.reasoningEffort`), `role`, `mode`, `title` and `clientRequestId`. It runs the child in
  the parent's checkout by default (`isolation: shared`) and inherits the parent's `runtimeMode`.
  The child's report comes back as `summary`, on the call result and on `task_status`. A child
  that asks a question wakes the parent, and the result carries `hasPendingQuestion`
  (pingdotgg/t3code#19521, #19538); `t3_pending_request_read` and `t3_pending_request_respond`
  answer it. A Claude subagent can call it too. Source: `packages/contracts/src/orchestratorMcp.ts`. Read-only review
  is a prompt rule (`agents/reviewer.md`), not something T3 enforces.
- **Used by:** `agents/models.md` § Reaching each model; `skills/code-review/SKILL.md` § Spawning
  a reviewer; `agents/reviewer.md`; `agents/research.md`
- **Breaks if:** `summary` stops carrying the child's report, a child's question stops waking
  the parent (it would wait forever), `clientRequestId` stops
  deduplicating a retry, the `target` shape or live model ids change, or children stop sharing
  the parent's checkout by default.

### login-shell-path

- **Relies on:** T3, and the Claude Code and Codex sessions it starts, inherit PATH from the
  desktop login session, so a line in `~/.profile` reaches the agent's shell.
- **Used by:** `hooks/check-tool-path.sh` (the SessionStart warning)
- **Breaks if:** T3 starts agent sessions with a shell environment of its own, so `~/.profile` no
  longer reaches them.

### session-hooks-loaded

- **Relies on:** the Claude Code and Codex sessions T3 starts load the user-level hooks
  (`~/.claude/settings.json`, `~/.codex/hooks.json`) as well as the project's. Not checked in T3
  source.
- **Used by:** `hooks/`; `install.sh`
- **Breaks if:** T3 starts sessions with a settings or config home of its own, so the user-level
  hooks no longer load.

### scheduled-reviews

- **Relies on:** T3 scheduled tasks (`schedule_task`, `fixed_time`, `bindToCurrentThread: false`)
  start a fresh thread on this repo's project, in its own worktree from `main`, and run a prompt
  that points at a skill here: "Weekly upstream review" on Mondays at 09:00
  (`skills/upstream-review/SKILL.md`), and "T3 update review" daily at 09:00
  (`skills/t3-update-review/SKILL.md`). Each opens its bookkeeping PR from that thread.
- **Used by:** `skills/upstream-review/SKILL.md` § Cadence; `skills/t3-update-review/SKILL.md`
  § Cadence
- **Breaks if:** scheduled runs stop starting when no thread is open, stop getting a worktree of
  their own, or the scheduler drops `fixed_time` tasks.

## Watching

### storage-cleanup-renamed-branches

- **Workaround:** `housekeeping` sweeps a T3 worktree whose branch was renamed, once its PR is
  merged or closed and its tree is clean. T3 keeps it even when its thread is deleted.
- **Used by:** `skills/housekeeping/SKILL.md` § 1
- **Would improve if:** T3's merged-worktree cleanup removes a worktree whose branch was renamed
  after the thread started. Today it keeps one with "repository or branch changed"
  (`apps/server/src/storageCleanup.ts`).
- **Watch:** pingdotgg/t3code#16559 and #17813 (open); #11078 (open; the sidebar keeps the
  creation-time branch name after a rename)

### storage-cleanup-archived-threads

- **Workaround:** `housekeeping` sweeps an archived thread's worktree once its PR is merged or
  closed and its tree is clean; deleting the thread also hands it to T3 (`worktreeOnDelete`).
- **Used by:** `skills/housekeeping/SKILL.md` § 1
- **Would improve if:** T3's storage cleanup sees archived threads' worktrees, so they are removed
  by the rules the user has set.
- **Watch:** pingdotgg/t3code#17811 (open); fix PR pingdotgg/t3code#16473 (open). Since
  pingdotgg/t3code#15208 the cleanup code says "Active threads only: archived threads are not
  candidates", so the fix runs against a maintainer's stated choice and may never land. Deleting
  a finished thread instead of archiving it hands its worktree to T3.

### storage-cleanup-stack-layers

- **Workaround:** `housekeeping` sweeps a worktree whose PR merged into another PR's branch, since
  T3 counts only merges into the default branch (`storageCleanupPullRequestMerged`).
- **Used by:** `skills/housekeeping/SKILL.md` (the stack-layer row)
- **Would improve if:** T3's merged-worktree cleanup accepts a PR merged into a stack parent.
- **Watch:** pingdotgg/t3code#14758 (open)

### storage-cleanup-orphan-folders

- **Workaround:** `housekeeping` removes a folder in T3's managed folder that no thread uses, once
  it holds no uncommitted work and its branch's PR is merged or closed. T3 lists such folders, with
  their sizes, under Settings → Storage → Last run (pingdotgg/t3code#19749), but never removes
  them, and the report has no MCP tool.
- **Used by:** `skills/housekeeping/SKILL.md` (the orphan-folder row)
- **Would improve if:** T3's cleanup removes an orphan folder by the same rules as a thread's
  worktree, or offers it to the user to remove.
- **Watch:** `apps/server/src/storageCleanup.ts`; no upstream issue found yet

### worktree-remove-hook

- **Workaround:** a project's per-worktree resources (a database) are swept by `housekeeping`
  through `docs/agents/housekeeping.md`, because T3 runs no script when it removes a worktree:
  `t3.json` has `runOnWorktreeCreate` and `runOnSettle`, and nothing on removal.
- **Used by:** `skills/housekeeping/SKILL.md` (the resources row); `contract.md` (the
  `housekeeping.md` row)
- **Would improve if:** `t3.json` gains a script T3 runs in or for a worktree it is about to
  remove; then each project moves its teardown there and the resources row moves to T3.
- **Watch:** `packages/contracts/src/t3ProjectFile.ts`; no upstream issue found yet

### implementer-worktrees

- **Workaround:** `implement-spec` runs each implementer as an Agent-tool worktree under
  `.claude/worktrees/`, sets it up by hand (`agents/implementer.md` step 2), and removes it itself
  (`skills/implement-spec/SKILL.md` § 3 step 4, and § 4 step 6).
- **Used by:** `agents/implementer.md`; `skills/implement-spec/SKILL.md`;
  `skills/implement/THREADS.md` (the exception)
- **Would improve if:** a `delegate_task` child with `isolation: worktree` (a checkout of the
  parent's local commit, with project setup done before the child starts) can commit to its own
  named branch that the orchestrator merges. Its result has no branch field today
  (`OrchestratorMcpDelegateTaskResult` in `packages/contracts/src/orchestratorMcp.ts`). Not tried
  yet: needs a trial.
- **Watch:** `apps/server/src/mcp/toolkits/orchestrator/tools.ts` (`delegate_task`)

### pr-watch-unreported-checks

- **Workaround:** `babysit-pr` reads the round on every wake and treats a required check not
  reported yet, a check still running or `mergeStateStatus` `UNKNOWN` as not ready, then waits on
  a fresh push with the background `gh pr checks --watch` loop.
- **Used by:** `skills/babysit-pr/SKILL.md` § 2 (the background wait and the state table)
- **Would improve if:** `watch_pull_request` wakes the thread when a required check has not
  reported.
- **Watch:** pingdotgg/t3code#18047 (open); #17831 (closed without merging on 2026-10-14)

### pr-watch-behind-base

- **Workaround:** `babysit-pr` sees `BEHIND` only when it reads the round on another wake, then
  updates once (§ 4b). A PR handed back READY that falls behind later is the user's to update, or
  the launcher's when it holds the merge.
- **Used by:** `skills/babysit-pr/SKILL.md` § 2 (the `BEHIND` row) and § 4b
- **Would improve if:** `watch_pull_request` wakes the thread when the PR's merge state becomes
  `BEHIND`.
- **Watch:** pingdotgg/t3code#18047, the same proposal as `pr-watch-unreported-checks`

### pr-watch-unresolved-threads

- **Workaround:** `babysit-pr` reads the round itself before the first `watch_pull_request` call
  and on every wake: unresolved threads, review-body findings and red checks.
- **Used by:** `skills/babysit-pr/SKILL.md` § 2
- **Would improve if:** `watch_pull_request` wakes on unresolved review threads that the branch's
  resolution rules hold open.
- **Watch:** pingdotgg/t3code#17703 (open)

### preview-tools-verification

- **Workaround:** projects drove UI verification with a browser CLI (`playwright-cli`) because
  T3's preview screenshots blurred mid-animation and clicks failed when a menu closed in between.
  On trial since 2026-10-15: in a T3 thread, `implement` step 4 drives with the preview tools
  (`skills/implement/PREVIEW.md`), each `preview_snapshot` capture after a `preview_wait_for`,
  and the final report notes where they fell short. rubens runs the trial first.
- **Used by:** `skills/implement/PREVIEW.md`; `skills/implement/SKILL.md` § 4; `contract.md`
  (the `verification.md` row)
- **Would improve if:** after ten verified PRs on rubens, no capture is blurred, no click is
  lost, console errors are read from the snapshot diagnostics, and recordings cover motion. Then
  each project's `verification.md` drops the browser CLI and its install, and this entry is
  resolved.
- **Watch:** `apps/server/src/mcp/toolkits/preview/tools.ts`; the trial's notes in the final
  reports of rubens' PRs

### pr-auto-link

- **Workaround:** the session calls `link_pull_request` right after `gh pr create`.
- **Used by:** `skills/implement/THREADS.md` ("One thread, one branch, one PR");
  `skills/implement/SKILL.md` § 7; `skills/implement-spec/SKILL.md` § 3 step 3
- **Would improve if:** T3 links a PR opened from the thread's branch with `gh`, without a call.
  Today the tool says to register "every pull request you open ... right after creating it",
  which implies it does not.
- **Watch:** `packages/contracts/src/threadPullRequest.ts` (`ThreadPullRequestLinkSource` has no
  branch-detected value)

## Ready

### storage-cleanup-settled-threads

- **Workaround:** a settled thread whose PR never merged (closed, abandoned, read-only work) keeps
  its worktree until `housekeeping` lists it as never-committed or closed.
- **Used by:** `skills/housekeeping/SKILL.md` § 1
- **Met in:** 0.0.46-nightly.20261015.3145: `worktreeSettledAfterDays` removes a worktree a set
  number of days after its thread settles (pingdotgg/t3code#15208; off by default). Since
  pingdotgg/t3code#19748 it also covers a thread whose reviewers shared its checkout.
- **Adopting means:** the user sets it (around 3 days) in Settings → Storage; then
  `housekeeping` § 1 checks it as it checks the merge and delete rules. A settled thread is
  finished, so its resources going with it is what we want; resuming it recreates the worktree
  and reruns setup, on the kept branch.

## Resolved

### housekeeping-worktree-removal

- **Workaround:** `housekeeping` removed finished thread worktrees itself, after the user accepted
  the list (`git worktree remove`).
- **Met in:** 0.0.46-nightly.20261014.3105 (pingdotgg/t3code#17563, merged 2026-10-10; closes
  pingdotgg/t3code#13836)
- **Adopted:** in each project, with storage cleanup turned on; what the sweep relies on since is
  `storage-cleanup-removes-thread-worktrees`.
