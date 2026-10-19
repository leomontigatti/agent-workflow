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

### auto-pull-default

- **Relies on:** T3's Automatically pull (Settings → Source Control) fast-forwards a project's
  main checkout only when it is on the default branch with no changed or untracked files and no
  local commits (`docs/user/project-settings.md` § Keep the default branch current).
- **Used by:** `skills/implement/THREADS.md` (the main checkout stays on the default branch)
- **Breaks if:** it pulls a checkout with local changes or commits, or pulls another branch.

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
  Since 2026-10-16 the user also runs `worktreeAfterDays: 5`, `worktreeSettledAfterDays: 5`,
  `worktreeUnchanged: true` and `browserArtifactsAfterDays: 5`. The first and third remove a
  paused thread's worktree, and T3 recreates it from the kept branch on resume, so `housekeeping`
  judges branches and resources by the live thread (`t3_thread_list`, then `t3_thread_read` for its
  branch), not by the worktree. Since pingdotgg/t3code#20449 (0.1.1-nightly.20261017.3272) T3
  recreates a missing worktree only at `<managed folder>/<repo>/<folder>`, compared by real path
  (`makeIsManagedWorktreePath` in `apps/server/src/worktreesDirectory.ts`); a thread bound to a
  folder outside it fails its turn instead, and `t3_worktree_handoff` no longer takes `path`.
- **Breaks if:** the settings are reset or the merge and delete rules turned off; T3 stops
  recreating a removed worktree from its branch on resume, or deletes the branch; T3 moves its managed folder, so `housekeeping` would take T3's worktrees for its
  own; T3 again keeps every worktree a subagent shares, so each reviewed thread's worktree stays;
  or the Last run report moves or stops giving a reason.

### thread-launch-workspace

- **Relies on:** `t3_thread_launch` with a `workspaceStrategy` (`worktree` with `baseRef`,
  `branch` and `startFromOrigin`; `existing_worktree`; `root`) creates or picks the checkout, binds
  the new thread to it and runs project setup before the agent starts, so a session never needs
  `git worktree add` (T3's orchestration instructions;
  `packages/provider-core/src/server/orchestrationInstructions.ts`).
- **Used by:** `skills/implement/THREADS.md` ("Work where you started", "A launched thread
  reports to its own inbox")
- **Breaks if:** the tool or its `workspaceStrategy` shape changes, or a launched thread stops
  getting a worktree of its own.

### renamed-branch-in-thread

- **Relies on:** a thread keeps working after its worktree's branch is renamed with
  `git branch -m`, and a PR linked by URL or number keeps its status. The link carries no branch
  name (`PullRequestTargetInput` in `apps/server/src/mcp/toolkits/pullRequests/tools.ts`). Only
  T3's automatic branch association follows the branch: since pingdotgg/t3code#20223
  (0.1.1-nightly.20261018.3331) a merged or closed PR it found is dropped once its head branch is
  no longer the thread's; explicit links keep theirs (`ThreadPullRequestService.ts`).
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

### own-thread-readable

- **Relies on:** `t3_thread_list` returns the caller's `currentThreadId`, and `t3_thread_read` on
  it returns the thread's user and assistant messages, including those from before a compaction,
  and `pullRequests`, every linked PR with its `url`, `source` and `state` (null until read from
  the host; pingdotgg/t3code#17454, since 0.1.1-nightly.20261018.3331). `linkedPullRequest` is the
  legacy single link and can be null meanwhile (`OrchestratorMcpThreadPullRequest` in
  `packages/contracts/src/orchestratorMcp.ts`).
- **Used by:** `skills/implement/THREADS.md` ("A lost context is recovered from T3")
- **Breaks if:** `currentThreadId` is dropped from the list result, a thread's timeline stops
  holding messages from before a compaction, or `t3_thread_read` stops returning `pullRequests`.

### pr-watch-is-native

- **Relies on:** `watch_pull_request` links the PR if needed, has T3 check it about every two
  minutes, and wakes the thread on a failed check, passed required checks, a new or edited
  comment or review, or a conflict with the base. Only comments posted after the call wake the
  thread. Watching a PR again starts from the check and conflict state the last watch reported,
  so it does not repeat news the thread already got (`endedWatch`, pingdotgg/t3code#21155, since
  0.1.1-nightly.20261018.3331). A subagent thread cannot call it. `unwatch_pull_request` ends the watch and returns the
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
  answer it. Since 0.1.1-nightly.20261018.3331 `summary` is the child's newest assistant message
  (pingdotgg/t3code#19058). `task_cancel` stops a child, and the tasks it delegated, and since
  0.1.1-nightly.20261019.3348 also cancels the task's own queued turn (pingdotgg/t3code#21487). `orchestrator_capabilities`
  lists the live provider instances and model ids. A Claude subagent can call `delegate_task`
  too, but only while the parent's run is active: unlike the other T3 tools, it is still refused
  (`parent_not_active`) to a background subagent once the parent's turn ended
  (pingdotgg/t3code#19751). Source: `packages/contracts/src/orchestratorMcp.ts`. Read-only review
  is a prompt rule (`agents/reviewer.md`), not something T3 enforces.
- **Used by:** `agents/models.md` § Reaching each model; `skills/code-review/SKILL.md` § Spawning
  a reviewer; `agents/reviewer.md`; `agents/research.md`
- **Breaks if:** `summary` stops carrying the child's report, a child's question stops waking
  the parent (it would wait forever), `clientRequestId` stops
  deduplicating a retry, the `target` shape or live model ids change, or children stop sharing
  the parent's checkout by default.

### background-subagents-keep-t3-tools

- **Relies on:** a Claude subagent started with the Agent tool runs in the background by default,
  and keeps calling T3 tools (the preview tools, `html_render`, `t3_thread_send`) with its
  parent thread's credential after the parent's turn ended, for as long as T3 lists it as a
  running background subagent of the same provider instance (pingdotgg/t3code#19751, since
  0.1.1-nightly.20261017.3238; `isLiveCallerShell` in
  `apps/server/src/mcp/OrchestratorMcpService.ts`, `assertLiveCaller` in
  `apps/server/src/mcp/threadAccess.ts`). Before that build, such a call failed with
  `parent_not_active`. Still refused: `delegate_task`, `create_threads` and `request_secret`,
  and any call from a subagent that finished and was resumed by its own background task. After
  a restart, T3 now wakes a thread whose subagent's background work the restart cut
  (pingdotgg/t3code#19750).
- **Used by:** `skills/implement/PREVIEW.md` § The loop step 1 (parallel subagents each open their
  own tab); `skills/implement-spec/SKILL.md` § 2 (the orchestrator ends its turn while its
  background implementers run)
- **Breaks if:** T3 again ties a caller's tools to the parent's active run, so a background
  subagent's preview calls fail once the parent's turn ends.

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
  start a fresh thread on this repo's project, in its own T3 worktree from `origin/main` (a task
  made over MCP gets `{baseRef: "main", startFromOrigin: true}`, which is this repo's default
  branch; `scheduledTaskWorkspaceStrategy` in `apps/server/src/mcp/OrchestratorMcpService.ts`;
  `apps/server/src/scheduledTasks/ScheduledTaskService.ts`), and run a prompt
  that points at a skill here: "Weekly upstream review" on Mondays at 09:00
  (`skills/upstream-review/SKILL.md`), and "T3 update review" daily at 09:00
  (`skills/t3-update-review/SKILL.md`). Each opens its bookkeeping PR from that thread.
- **Used by:** `skills/upstream-review/SKILL.md` § Cadence; `skills/t3-update-review/SKILL.md`
  § Cadence
- **Breaks if:** scheduled runs stop starting when no thread is open, stop getting a worktree of
  their own, the MCP default base stops being `main`, or the scheduler drops `fixed_time` tasks.
  A project whose default branch is not `main` sets the task's Base branch in Settings →
  Scheduled tasks (pingdotgg/t3code#16183).

### update-review-reads-t3

- **Relies on:** `t3_environment_read` returns the installed build as `serverVersion`, a nightly
  tag that is also a release name on pingdotgg/t3code, and `t3_project_list` returns each
  project's `workspaceRoot`, a git checkout whose `origin` is the project's repo.
- **Used by:** `skills/t3-update-review/SKILL.md` steps 1 and 3;
  `skills/t3-update-review/scripts/changes.py`
- **Breaks if:** `serverVersion` stops matching a release tag, so `changes.py` finds no range, or
  the project list stops giving a checkout path.

## Watching

### scheduled-run-status

- **Workaround:** a scheduled run is read from its thread, never from the task's
  `lastRunStatus`: the scheduler records `succeeded` once the launch returns, whatever the run
  does next (`apps/server/src/scheduledTasks/ScheduledTaskService.ts`). A run's thread without a
  report, or a bookkeeping PR that never appeared, is a failed run.
- **Used by:** `skills/upstream-review/SKILL.md` § Cadence; `skills/t3-update-review/SKILL.md`
  § Cadence
- **Would improve if:** a run that fails or ends without its result is recorded as failed.
- **Watch:** pingdotgg/t3code#17889 (open)

### t3json-manual-import

- **Workaround:** each project's `t3.json` is imported once per T3 install (project settings →
  Actions → Import from t3.json); until then T3 runs no setup, and `agents/implementer.md` step 2
  is the same script by hand.
- **Used by:** `skills/implement/THREADS.md`; `agents/implementer.md` step 2
- **Would improve if:** T3 reads `runOnWorktreeCreate` from the checked-in `t3.json` without an
  import (`setupProjectScript` in `packages/shared/src/projectScripts.ts` sees only imported
  scripts).
- **Watch:** pingdotgg/t3code#5063 (closed 2026-08-15, yet the runner still reads only imported
  scripts)

### storage-cleanup-renamed-branches

- **Workaround:** `housekeeping` sweeps a T3 worktree whose branch was renamed, once its PR is
  merged or closed and its tree is clean. T3 keeps it even when its thread is deleted.
- **Used by:** `skills/housekeeping/SKILL.md` § 1
- **Would improve if:** T3's merged-worktree cleanup removes a worktree whose branch was renamed
  after the thread started. Today it keeps one with "Repository or branch changed", or with "A
  subagent thread's branch differs from this worktree's branch" when the rename happened before
  pingdotgg/t3code#20079 (0.1.1-nightly.20261016.3203), which now renames the subagents' branch
  too (`apps/server/src/storageCleanup.ts`). On 2026-10-16, 28 worktrees were kept, most for one
  of these two reasons.
- **Watch:** pingdotgg/t3code#16559 and #17813 (open); #11078 (open; the sidebar keeps the
  creation-time branch name after a rename)

### storage-cleanup-archived-threads

- **Workaround:** `housekeeping` sweeps an archived thread's worktree once its PR is merged or
  closed and its tree is clean; deleting the thread also hands it to T3 (`worktreeOnDelete`).
- **Used by:** `skills/housekeeping/SKILL.md` § 1
- **Would improve if:** T3's storage cleanup sees archived threads' worktrees, so they are removed
  by the rules the user has set.
- **Watch:** fix pingdotgg/t3code#16473, merged 2026-10-19 (`034b506`; closes #17811), after
  0.1.1-nightly.20261019.3373 was cut, so the next nightly should carry it: cleanup then reads
  archived threads as candidates and as sharers. Ready once the installed build includes it.

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
  them, and the report has no MCP tool. `t3_worktree_list` cannot find them either: it lists
  git's branch refs and the checkout each one is in, with no thread and no detached worktree
  (seen on 2026-10-17), so an orphan on a branch is listed like any other. An orphan is a folder
  no live thread's `worktreePath` (from `t3_thread_read`) names.
- **Used by:** `skills/housekeeping/SKILL.md` (the orphan-folder row, and step 1's orphan rule)
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
  yet: needs a trial. Since pingdotgg/t3code#20213 such a call is refused when the project's repo
  lacks the parent checkout's commit.
- **Watch:** `apps/server/src/mcp/toolkits/orchestrator/tools.ts` (`delegate_task`)

### pr-watch-unreported-checks

- **Workaround:** `babysit-pr` reads the round on every wake and treats a required check not
  reported yet, a check still running or `mergeStateStatus` `UNKNOWN` as not ready, then waits on
  a fresh push with the background `gh pr checks --watch` loop.
- **Used by:** `skills/babysit-pr/SKILL.md` § 2 (the background wait and the state table)
- **Would improve if:** `watch_pull_request` wakes the thread when a required check has not
  reported, and once every check has finished rather than only on a failure or on all required
  checks passing; then the background `gh pr checks --watch` wait goes.
- **Watch:** pingdotgg/t3code discussions/18047 (open); #16924 (open); #17831 (closed without merging on
  2026-10-14)

### pr-watch-behind-base

- **Workaround:** `babysit-pr` sees `BEHIND` only when it reads the round on another wake, then
  updates once (§ 4b). A PR handed back READY that falls behind later is the user's to update, or
  the launcher's when it holds the merge.
- **Used by:** `skills/babysit-pr/SKILL.md` § 2 (the `BEHIND` row) and § 4b
- **Would improve if:** `watch_pull_request` wakes the thread when the PR's merge state becomes
  `BEHIND`.
- **Watch:** pingdotgg/t3code discussions/18047, the same proposal as `pr-watch-unreported-checks`

### pr-watch-unresolved-threads

- **Workaround:** `babysit-pr` reads the round itself before the first `watch_pull_request` call
  and on every wake: unresolved threads, review-body findings and red checks.
- **Used by:** `skills/babysit-pr/SKILL.md` § 2
- **Would improve if:** `watch_pull_request` wakes on unresolved review threads that the branch's
  resolution rules hold open.
- **Watch:** pingdotgg/t3code#17703 (open)

### preview-tools-verification

- **Workaround:** projects drove UI verification with a browser CLI (`playwright-cli`) because
  T3's preview screenshots blurred mid-animation, the viewport resized itself and clicks failed
  when a menu closed in between. On trial since 2026-10-15: in a T3 thread, `implement` step 4
  drives with the preview tools (`skills/implement/PREVIEW.md`), and the final report notes where
  they fell short. en-escena's probe on 2026-10-16 found the three old faults gone (no viewport
  drift in 10 reads, 6 of 6 menu clicks landed, no capture caught mid-transition) and two
  capture faults in their place, both from one cause. `preview_snapshot` caps the PNG at
  1280 px wide (`MAX_SCREENSHOT_WIDTH`, hardcoded, no option), so any viewport wider than
  640 CSS px is captured through a scaled CDP clip: a 1440 design width comes out shrunk, and a
  `backdrop-filter` blur renders as mirrored tiles of the page's top-left corner (checked
  2026-10-17: tiled at the default 1280×800, correct at 640×400). So a project whose dialogs blur
  their backdrop, or whose design width is over 1280, takes its images with its browser CLI (its
  `verification.md` § Evidence says so). Recordings capture unscaled: a frame from one is
  full-size (2×) and renders the blur correctly, but extracting it needs an MP4 decoder (no
  system `ffmpeg`; Playwright's bundled one reads no MP4) and is lossy, so the browser CLI stays.
  The tools need "Agent browser access" on in Settings and, on Ubuntu 23.10+, a one-time
  `sudo t3 browser setup`; both were missing until 2026-10-16, so no thread used them before.
- **Used by:** `skills/implement/PREVIEW.md`; `skills/implement/SKILL.md` § 4; `contract.md`
  (the `verification.md` row)
- **Would improve if:** both hold, in the installed T3: a snapshot renders `backdrop-filter`
  correctly at a desktop viewport (pingdotgg/t3code#20899), and it saves at the viewport's size
  or the user accepts images 1280 px wide. A fix to #20899 alone leaves this entry
  **watching** while the cap stands; ask the user about the 1280 px images. **Ready** only once
  en-escena's dialog probe passes (`/administracion/resultados`, Acciones → Descargar,
  1440×900). Adoption is then two steps: first each project's § Evidence
  takes its images with `preview_snapshot`, keeping the browser CLI installed; once ten PRs
  verified that way had no lost click, each `verification.md` drops the browser CLI and its
  install, and this entry is resolved.
- **Watch:** pingdotgg/t3code#20899 (the blur; no issue asks to lift the size cap, and #10141,
  which tried, closed unmerged); `apps/server/src/preview/ServerBrowserPage.ts`
  (`MAX_SCREENSHOT_WIDTH`, `captureViewport`); `apps/server/src/mcp/toolkits/preview/tools.ts`;
  the trial's notes in the final reports of en-escena's and rubens' PRs

### pr-auto-link

- **Workaround:** the session calls `link_pull_request` right after `gh pr create`.
- **Used by:** `skills/implement/THREADS.md` ("One thread, one branch, one PR");
  `skills/implement/SKILL.md` § 7; `skills/implement-spec/SKILL.md` § 3 step 3
- **Would improve if:** T3 links a PR opened from the thread's branch with `gh`, without a call.
  Today the tool says to register "every pull request you open ... right after creating it",
  which implies it does not.
- **Watch:** `packages/contracts/src/threadPullRequest.ts` (`ThreadPullRequestLinkSource` has no
  branch-detected value). A lead: T3 already finds a thread's PR by its branch after each turn and
  keeps it as `branchPullRequest`, apart from the links (discovery in
  `apps/server/src/orchestration-v2/ThreadPullRequestService.ts`; pingdotgg/t3code#20223 shows it
  in the sidebar). Whether that association settles the thread on merge and can be watched is
  untested: needs a trial with a PR opened by `gh` and never linked.

## Ready

None.

## Resolved

### setup-runs-in-main-checkout

- **Workaround:** a "local" thread, with no worktree, ran the `runOnWorktreeCreate` script in the
  main checkout; `skills/implement/THREADS.md` said a failed setup terminal there was expected.
- **Met in:** 0.1.1-nightly.20261018.3331 (pingdotgg/t3code#18891; closes #18882). An
  `existing_worktree` launch on the project root still runs the script, so `contract.md`'s
  `t3.json` row keeps it safe to run in the main checkout.
- **Adopted:** 2026-10-19; the sentence left `THREADS.md` and the contract row names the
  `existing_worktree` case.

### thread-read-lists-prs

- **Workaround:** recovering a lost context called `list_thread_pull_requests` after
  `t3_thread_read` for the thread's PRs.
- **Met in:** 0.1.1-nightly.20261018.3331 (pingdotgg/t3code#17454: `pullRequests` on
  `t3_thread_read` and `t3_thread_list`).
- **Adopted:** 2026-10-19; "A lost context is recovered from T3" takes them from `t3_thread_read`,
  and `own-thread-readable` relies on that.

### storage-cleanup-settled-threads

- **Workaround:** a settled thread whose PR never merged kept its worktree until `housekeeping`
  listed it.
- **Met in:** 0.0.46-nightly.20261015.3145 (`worktreeSettledAfterDays`, pingdotgg/t3code#15208)
- **Adopted:** 2026-10-16, at 5 days; part of `storage-cleanup-removes-thread-worktrees` since.

### housekeeping-worktree-removal

- **Workaround:** `housekeeping` removed finished thread worktrees itself, after the user accepted
  the list (`git worktree remove`).
- **Met in:** 0.0.46-nightly.20261014.3105 (pingdotgg/t3code#17563, merged 2026-10-10; closes
  pingdotgg/t3code#13836)
- **Adopted:** in each project, with storage cleanup turned on; what the sweep relies on since is
  `storage-cleanup-removes-thread-worktrees`.
