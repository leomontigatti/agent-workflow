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
  Import from t3.json). Since 0.1.4-nightly.20261027.3796 the runner skips the script
  (`skipped-for-link`) for a thread a linked environment started under a link below full access
  (`ProjectSetupScriptRunner.ts`); linked environments are a Labs beta, off by default
  (`linkedEnvironmentsEnabled`), and no workflow here uses them. Since pingdotgg/t3code#31857
  (0.1.8-nightly.20261106.4262) a script may set `stopOnSettle`, which stops its terminal and child
  processes when the thread settles; it defaults to false and no project's `t3.json` sets it.
- **Used by:** `skills/implement/THREADS.md`; `agents/implementer.md` step 1 (T3 set up the
  implementer's checkout before it started)
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
  `skills/housekeeping/SKILL.md` (the worktrees the sweep owns)
- **Breaks if:** T3's cleanup starts removing worktrees outside its managed folder, which would
  race the removal `housekeeping` does itself.

### storage-cleanup-removes-thread-worktrees

- **Relies on:** T3's storage cleanup is on (`storageCleanup` in `~/.t3/userdata/settings.json`:
  `worktreeOnMerge: true`, `worktreeOnDelete: true`; `worktreeKeepWhen` left at its default,
  `uncommitted-changes`). Hourly, at startup and on a settings change, it removes a worktree in
  its managed folder (`~/.t3/worktrees/<project>/`) once the thread's PR merges into the default
  branch or its last thread is deleted, archived threads included (pingdotgg/t3code#16473, since
  0.1.1-nightly.20261020.3386), keeps one with uncommitted changes, an open terminal, a running
  or queued thread or an open provider session, or, since pingdotgg/t3code#24689 (0.1.6-nightly.20261031.3973), a thread held
  for its usage-limit reset, and reports why it kept each one under Settings →
  Maintenance → Cleanup → Last run; its rules sit under Settings → Worktrees → Cleanup (both were
  Settings → Storage until pingdotgg/t3code#25651, 0.1.3-nightly.20261027.3748, which redirects
  the old page). A worktree other threads share is
  kept, unless every one of them is a subagent of the same parent, whose rules then decide
  (pingdotgg/t3code#19748, since 0.1.1-nightly.20261016.3203): that is what lets a thread whose
  reviewers ran through `delegate_task` in its checkout be removed. Since pingdotgg/t3code#26901
  (0.1.6-nightly.20261031.3969) a side chat counts in that chain too (`worktreeOwner`). Since
  0.1.3-nightly.20261023.3592 a deleted thread still owns a worktree its remaining subagents share,
  so `worktreeOnDelete` removes it too (pingdotgg/t3code#23900). Deleting a thread always
  requests a sweep; since pingdotgg/t3code#26038 (0.1.6-nightly.20261029.3892) a provider session
  stop requests one only while a deleted thread's worktree waits on it, and the other worktree
  rules run on the hourly sweep; since 0.1.8-nightly.20261106.4262 a provider session's error
  requests one only once that session is no longer live. Last run also lists folders
  in the managed folder no thread uses (pingdotgg/t3code#19749), which T3 never removes. It keeps
  the branch on purpose, runs no script on removal, and has no MCP tool to trigger or read it
  (`apps/server/src/storageCleanup.ts`; `packages/contracts/src/settings.ts`;
  `docs/user/project-settings.md` § Storage cleanup). Since pingdotgg/t3code#27175
  (0.1.7-nightly.20261102.4061) a repository with no remote is judged against its checked-out
  branch; every project here has a remote, so its path is unchanged. Since
  pingdotgg/t3code#30026 (0.1.7-nightly.20261104.4151) `worktreeSettledAfterDays` also removes a
  subagent's own worktree (a `delegate_task` child's `isolation: worktree` checkout), aged from
  the nearest settled ancestor through subagent lineage, every ancestor on the way idle and
  rechecked before removal (`worktreeSettlementChain`); a pinned or explicitly active thread stops
  the chain. Before, such a worktree was kept forever. `implement-spec` § 4 still removes each
  implementer's worktree itself, so this catches only what it misses. Since
  pingdotgg/t3code#32933 (0.1.8-nightly.20261109.4392) a sweep checks age before any Git read and
  measures a worktree's size outside its checkout lease, then rechecks path, activity, branch,
  commit, changes and settings inside the lease before removing; with `worktreeOnMerge` on, as
  here, every worktree still gets the Git checks, and the keep reasons read as before. Since
  pingdotgg/t3code#31069 (0.1.10-nightly.20261112.4564) a worktree with an edit git status hides
  (an `assume-unchanged` or `skip-worktree` file whose content differs) is kept, as "has
  uncommitted changes hidden from git status (<file>)"; since #26593 (0.1.10-nightly.20261111.4529)
  one whose status or ignored-file listing outgrows the inspection limit is kept too. Since
  pingdotgg/t3code#19665 (0.1.10-nightly.20261111.4544) a subagent thread settles with its
  parent, once idle, instead of on its own inactivity or PR rules; that settlement is what
  `worktreeSettledAfterDays` ages a child's own worktree from, as above.
- **Used by:** `skills/housekeeping/SKILL.md` (its table, and step 1 reads the settings);
  `skills/implement/THREADS.md` ("Leaving a worktree behind is fine")
  Since 2026-10-16 the user also runs `worktreeAfterDays: 5`, `worktreeSettledAfterDays: 5`,
  `worktreeUnchanged: true` and `browserArtifactsAfterDays: 5`. The first and third remove a
  paused thread's worktree, and T3 recreates it from the kept branch on resume, tracked files only
  (`rebuilt-worktree-no-setup`), so `housekeeping`
  judges branches and resources by the live thread (`t3_thread_list`, then `t3_thread_read` for its
  branch), not by the worktree. Since pingdotgg/t3code#20449 (0.1.1-nightly.20261017.3272) T3
  recreates a missing worktree only at `<managed folder>/<repo>/<folder>`, compared by real path
  (`makeIsManagedWorktreePath` in `apps/server/src/worktreesDirectory.ts`); a thread bound to a
  folder outside it fails its turn instead, and `t3_worktree_handoff` no longer takes `path`.
  Since pingdotgg/t3code#18359 (0.1.3-nightly.20261027.3748) a thread whose worktree and branch
  are both gone resumes too, on a branch recreated from the project's current named branch,
  without its old commits; before, it could never run another turn. Since
  pingdotgg/t3code#26758 (0.1.6-nightly.20261031.3969) recovery first restores the kept branch or its
  cached `origin/<branch>` tip, so pushed commits come back; with neither it takes the project
  branch, the cached remote default or a detached HEAD. So a live thread's branch is still never
  deleted.
- **Breaks if:** the settings are reset or the merge and delete rules turned off; T3 stops
  recreating a removed worktree from its branch on resume, or deletes the branch; T3 moves its managed folder, so `housekeeping` would take T3's worktrees for its
  own; T3 again keeps every worktree a subagent shares, so each reviewed thread's worktree stays;
  or the Last run report moves or stops giving a reason.

### thread-launch-workspace

- **Relies on:** `t3_thread_launch` with a `workspaceStrategy` (`worktree` with `baseRef`,
  `branch` and `startFromOrigin`; `existing_worktree`; `root`) creates or picks the checkout, binds
  the new thread to it and runs project setup before the agent starts, so a session never needs
  `git worktree add` (T3's orchestration instructions;
  `packages/provider-core/src/server/orchestrationInstructions.ts`). Since
  pingdotgg/t3code#21032 (0.1.1-nightly.20261020.3386) `startFromOrigin: true` fetches the base
  branch's own remote (`resolveWorktreeBaseRemote` in `ThreadLaunchService.ts`), not `origin` by
  name; every project here tracks `origin`, so nothing changes. Since pingdotgg/t3code#16654
  (0.1.4-nightly.20261027.3796) it takes an optional `clientRequestId`: a retry with the same key
  replays the accepted launch and returns the same thread, where before a lost reply meant
  checking `t3_thread_list` before launching again. Since pingdotgg/t3code#26682
  (0.1.6-nightly.20261031.3969) an inherited runtime mode steps down to one the provider offers, and an
  explicit unsupported one is refused, as `delegate_task` already did. Since
  pingdotgg/t3code#28582 (0.1.7-nightly.20261102.4061) the `startFromOrigin` fetch passes
  `--no-tags`, so a new thread's checkout can lag the remote's tags: read a tag from the remote.
  No project's `docs/agents/`, `.agents/`, `AGENTS.md` or `t3.json` runs `git describe`. Since
  pingdotgg/t3code#29781 (0.1.7-nightly.20261104.4151) a launch cancelled or failed before it
  records its workspace force-deletes the branch it created, renamed or not, with the worktree;
  since pingdotgg/t3code#28373 (0.1.7-nightly.20261103.4119) a failed `git worktree add` does too.
  A branch that existed before the call is never touched. Since pingdotgg/t3code#31819
  (0.1.8-nightly.20261106.4262) the `workspaceStrategy` description and T3's injected
  instructions give the base: honor a requested one, else independent work starts from the
  default branch as `origin/<default>` with `startFromOrigin: true`, and work that needs
  unpublished commits or depends on another branch starts from its local base with
  `startFromOrigin: false`. `THREADS.md` names no base, so it does not conflict. Since
  pingdotgg/t3code#32934 (0.1.8-nightly.20261109.4392) a generated worktree folder is a bounded
  prefix of the branch plus a digest of the shared git directory and branch (this review's own:
  `~/.t3/worktrees/agent-workflow/t3-b9f99963-6a1fe677a1bd3922`), still under
  `<managed folder>/<repo>/`; existing and explicit paths keep theirs. Folder names stay unique
  and keep their name on a branch rename, which rubens' and enescena's
  `worktree-folder-names-unique` rely on. Since pingdotgg/t3code#34781 (0.1.10-nightly.20261112.4580)
  a new worktree thread's agent starts only once T3's branch rename has landed, so
  `git branch --show-current` gives the final name from the first command; a rename that fails
  leaves the temporary `t3/<id>` name and, since #34813 (same build), a "Branch not renamed"
  notice in the thread. Since #29328 (0.1.10-nightly.20261111.4544) a launch is refused up front
  when an existing branch blocks the requested `branch` (`docs` against `docs/x`, or the
  reverse), with a sibling name to use; since #34279 (same build) a `worktree` launch in a
  project that is not a Git repository is refused; since #26625 (same build) a `modelSelection`
  the provider does not advertise is refused (aliases match). A `root` launch with no `branch`
  records the checkout's branch since #34812 (0.1.10-nightly.20261112.4580).
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
  no longer the thread's; explicit links keep theirs (`ThreadPullRequestService.ts`). Since
  pingdotgg/t3code#31599 (0.1.8-nightly.20261106.4247) the thread's recorded `branch` follows its
  worktree: when T3's VCS status cache sees the checked-out branch change, every thread on that
  worktree, archived ones too, gets the new name
  (`apps/server/src/orchestration-v2/WorktreeBranchSync.ts`, fed by
  `VcsStatusBroadcaster.streamBranchChanges`); a detached HEAD or a root checkout keeps the old
  one. So automatic association now follows the new branch.
- **Used by:** `skills/implement/THREADS.md` ("Branch names")
- **Breaks if:** T3 starts resolving a thread's PR, or its state, from the branch name recorded
  when the thread started.

### pr-linked-by-tool

- **Relies on:** `link_pull_request` accepts a PR URL, or repository and number; a repeat call
  returns `alreadyLinked`; the linked PR's status shows beside the thread, and the thread settles
  when the PR merges (`apps/server/src/mcp/toolkits/pullRequests/tools.ts`). Since
  0.1.3-nightly.20261027.3748 a delegated child's call also returns `next` ("End your reply with:
  PR <full URL>, head <SHA>, checks and reviews <state>.", pingdotgg/t3code#25423). Since
  pingdotgg/t3code#26983 (0.1.6-nightly.20261029.3892) the one-minute PR sweep skips subagent and
  delegate children: a child's PR is looked up only after its own run, checkpoint, metadata
  update, unsettle or unarchive, so a merge after that doesn't reach the child. `implement-spec`
  children open no PR, and storage cleanup asks the host itself
  (`gitManager.branchPullRequest` in `storageCleanup.ts`). Since 0.1.7-nightly.20261101.4016
  `link_pull_requests` takes `urls` and links several in one call (pingdotgg/t3code#27994), and
  `unlink_pull_requests` drops every PR in the given `states` (pingdotgg/t3code#27925); no skill
  uses either. T3's runtime instructions (`packages/provider-core/src/server/runtimeInstructions.ts`)
  still say "Host tools do not link for you", beside the auto-link `pr-auto-link` records; the
  extra call returns `alreadyLinked`. Since pingdotgg/t3code#32162 (0.1.8-nightly.20261106.4288)
  the PR sync's git reads run as background git work, so they no longer delay git status after a
  restart; what it links and reports is unchanged. Since pingdotgg/t3code#30071 (0.1.7-nightly.20261104.4151)
  the sync stops polling a link whose PR closed over a day ago; a requested sync or a seen state
  change still reads it, so a reopened PR is picked up. Since pingdotgg/t3code#33474
  (0.1.10-nightly.20261112.4564) `gh pr new` is auto-linked like `gh pr create`; since #34218
  (0.1.10-nightly.20261111.4544) automatic association no longer gives a new thread a PR that
  merged or closed before it was created, unless that PR is checked out; since #33095
  (0.1.10-nightly.20261112.4564) settling a thread refreshes its PR status once.
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
  `packages/contracts/src/orchestratorMcp.ts`). Since pingdotgg/t3code#26442
  (0.1.4-nightly.20261028.3824) `t3_thread_list` also takes `allProjects: true`, each item has its
  `projectId`, and the result's top-level `projectId` is `null` for an all-projects list; a call
  without the flag still lists the caller's project and returns `currentThreadId`. Since
  pingdotgg/t3code#34895 (0.1.10-nightly.20261112.4580) `pullRequests` holds only the links not yet
  merged or closed (a link whose state is still unread stays in), each with `watching` and
  `watchStartedAt`, and `pullRequestCount` counts every link; `t3_thread_read` carries them on
  the first page only (no `afterPosition` or `itemId`), and `list_thread_pull_requests` still
  lists every link with its state. So a thread whose PR merged reads an empty `pullRequests`
  with `pullRequestCount: 1`; `THREADS.md` reads the rest from `list_thread_pull_requests` since
  2026-11-12. Since #34674 (0.1.10-nightly.20261112.4564) `t3_thread_list` gives `status: waiting`
  for a thread whose turn ended on awaited background work.
- **Used by:** `skills/implement/THREADS.md` ("A lost context is recovered from T3", "One thread,
  one branch, one PR")
- **Breaks if:** `currentThreadId` is dropped from the list result, a thread's timeline stops
  holding messages from before a compaction, `t3_thread_read` stops returning the open
  `pullRequests`, or `list_thread_pull_requests` stops listing merged and closed links.

### pr-watch-is-native

- **Relies on:** `watch_pull_request` links the PR if needed, has T3 check it about every two
  minutes, and wakes the thread on a failed check, passed required checks, a new or edited
  comment or review, or a conflict with the base. Since 0.1.3-nightly.20261023.3566 it also wakes once the other checks
  finish after the required ones passed early (`owedChecks`, pingdotgg/t3code#23904), and, on
  GitHub, once when a head has had no checks for 15 minutes or more (`checksAwaitedSince`,
  pingdotgg/t3code#23863; `packages/contracts/src/threadPullRequest.ts`), within one 2-minute
  sweep of the deadline since pingdotgg/t3code#25437 (0.1.6-nightly.20261031.3973). Only comments posted
  after the call wake the thread. Watching a PR again starts from the check and conflict state the last watch reported,
  so it does not repeat news the thread already got (`endedWatch`, pingdotgg/t3code#21155, since
  0.1.1-nightly.20261018.3331). A subagent thread cannot call it: since
  0.1.3-nightly.20261025.3669 a `delegate_task` child no longer even sees the watch tools
  (pingdotgg/t3code#24808), and each wake says the PR stays linked and watched, so the session
  never calls the tool again on a wake (pingdotgg/t3code#24781). A watched PR keeps the thread in
  Working (pingdotgg/t3code#24610). `unwatch_pull_request` ends the watch and returns the
  thread to the user's inbox; it wakes no other thread. Since pingdotgg/t3code#26395
  (0.1.4-nightly.20261028.3822) a watch whose PR is already merged no longer counts as pending
  work, so the thread settles when the turn that merged ends, not on the watch's next 2-minute
  sweep; a closed PR still holds the thread, since its wake is still owed. Since
  pingdotgg/t3code#22022 (0.1.7-nightly.20261101.4048) T3 keeps a GitHub PR's last known
  mergeability while GitHub reports `unknown` and the PR's `updatedAt` is unchanged, so T3's
  stored state can differ from the `UNKNOWN` that `babysit-pr` reads from GitHub itself. Since
  pingdotgg/t3code#29767 (0.1.7-nightly.20261104.4151) a reported conflict belongs to one head, so
  a push that leaves the branch conflicting wakes the thread again. Since pingdotgg/t3code#30291
  (0.1.8-nightly.20261106.4262) a slow host no longer delays other watched PRs' wakes.
  `list_thread_pull_requests` with another thread's `threadId` lists that thread's PRs; since
  pingdotgg/t3code#30375 (same build) the PR tools fail a missing thread with `thread_not_found`,
  pointing a bare uuid at its `mcp:` thread. Since pingdotgg/t3code#32325
  (0.1.8-nightly.20261107.4314) inactivity auto-settle defaults to 7 days instead of 3; settings
  are stored sparse, so only a user on the default moves. This machine stores
  `sidebarAutoSettleAfterDays: null` (off), an explicit value the change keeps. Since
  pingdotgg/t3code#33134 (0.1.8-nightly.20261109.4392) T3 leaves out GitHub comments, reviews and
  inline comments a maintainer hid (`isMinimized`), so a hidden one wakes no watch and a hidden
  review no longer sets the review state; `babysit-pr` reads the round from GitHub itself and,
  since 2026-11-09, leaves them out too (`triage.md` § Reading the round). Since pingdotgg/t3code#32395 (0.1.8-nightly.20261107.4327) T3's review state
  follows GitHub's `reviewDecision` when GitHub gives one. Since pingdotgg/t3code#24599
  (0.1.9-nightly.20261110.4465) checks waiting on a maintainer's workflow approval wake the
  thread once per head ("checks await approval", `awaitingApproval` and `approvalAnnounced` in
  `threadPullRequest.ts`) instead of flapping between failed and passed; the projects here run
  no fork workflows. Since pingdotgg/t3code#33548 (0.1.9-nightly.20261111.4515) a watched
  github.com PR also re-reads on GitHub's event stream (push, review, merge, conflict), but only
  for a user signed in through T3's GitHub app, which is opt-in; checks have no events, so they
  still wait on the 2-minute sweep. This machine has no app sign-in in `settings.json`, so it
  still polls. Since pingdotgg/t3code#34624 (0.1.10-nightly.20261112.4564) a GitHub workflow run
  still queued with no jobs counts as a pending check, so a lone finished check (a skipped
  CodeRabbit) no longer wakes "checks passed" while CI waits to start. Since #21239
  (0.1.10-nightly.20261111.4529) a stale queued watch wake is dropped; since #27953
  (0.1.10-nightly.20261111.4544) a closed PR's watch ends even when the activity read fails; since
  #34884 (0.1.10-nightly.20261112.4580) a watch started after a pending self-settle survives the
  turn's end. `t3_thread_read` now shows each open PR's `watching` (`own-thread-readable`).
- **Used by:** `skills/babysit-pr/SKILL.md` § 2 and § 5; `skills/implement/SKILL.md` § 7;
  `skills/implement/THREADS.md` ("A launched thread reports to its own inbox");
  `skills/fan-out/SKILL.md` § 4
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
  (pingdotgg/t3code#19521, #19538); `t3_pending_request` with `action: "read"`, then
  `"respond"`, answers it (one tool since 0.1.3-nightly.20261027.3748, pingdotgg/t3code#25423;
  `t3_pending_request_read` and `_respond` before). Since 0.1.1-nightly.20261018.3331 `summary`
  is the child's newest assistant message (pingdotgg/t3code#19058). `task_cancel` stops a child, and the tasks it delegated, and since
  0.1.1-nightly.20261019.3348 also cancels the task's own queued turn (pingdotgg/t3code#21487).
  Since 0.1.1-nightly.20261020.3386 the result also carries the child's `options` and a
  `pendingApproval`, which ends a `mode: wait` early like a question. `orchestrator_capabilities`
  lists the live provider instances and model ids, from the composer's catalog: a model hidden in
  Settings (`providerModelPreferences.<instance>.hiddenModels`) is absent from it, yet
  `delegate_task` still runs it (checked 2026-10-21 with `claude-sonnet-5-5`, then hidden). Since
  0.1.2-nightly.20261021.3486 it lists a short set (pingdotgg/t3code#22889): every current
  Codex and Claude model (`FULL_CATALOG_DRIVERS`), plus favorites, custom models and the
  caller's own; a legacy model is found with `search`, and "delegate_task accepts any catalog
  model, listed or not". Since pingdotgg/t3code#26448 (0.1.4-nightly.20261028.3824) search words
  that name the provider are dropped before matching (`listCapabilityModels` in
  `OrchestratorMcpService.ts`), so they no longer narrow the list to a few stale models; since pingdotgg/t3code#26502
  (0.1.6-nightly.20261031.3969) only whole provider words are dropped, and part of one stays when a model
  matches it. Each model's options are `{id, values, default}`, and `label` is
  omitted when it restates the id. Every id in `agents/models.md` was listed on 2026-10-23. A Claude subagent can call `delegate_task`
  too, but only while the parent's run is active: unlike the other T3 tools, it is still refused
  (`parent_not_active`) to a background subagent once the parent's turn ended
  (pingdotgg/t3code#19751). Since 0.1.3-nightly.20261025.3669 a result for a task still running
  carries `next` ("Completion wakes this thread, so end your turn", pingdotgg/t3code#24782) and
  every result carries the child's thread `link` (pingdotgg/t3code#24784). Since
  0.1.4-nightly.20261027.3796 `childThreadId` is null for a task delegated to a linked
  environment (`target.environmentId`, then `remoteChild` names its thread there;
  pingdotgg/t3code#16719), and a local `target.projectId` other than the parent's is refused; a
  task in this environment still has its `childThreadId`. A child's question survives a server
  restart (pingdotgg/t3code#19229), and no longer flags the parent as waiting on the user
  (pingdotgg/t3code#26367). Since pingdotgg/t3code#27222 (0.1.6-nightly.20261030.3904) a restart
  continuation that fails before the provider took its prompt retries after 1 and 3 minutes, and
  a child's continuation stands down when the parent's run was stopped. Since
  pingdotgg/t3code#27252 (0.1.6-nightly.20261030.3917) a Stop is bounded at 15 s and Claude's and
  ACP's fallbacks no longer mark a turn stopped while the agent runs on: an agent that ignores it
  shows "Agent not responding to Stop" until the user presses Force stop, which is not an MCP
  tool. `task_cancel` dispatches that same `thread.stop`; what `task_status` shows for such a
  child was not checked. Since pingdotgg/t3code#16419 (0.1.7-nightly.20261101.4016) Claude's wait for the
  interrupt acknowledgement is bounded at 10 s, after which the query is closed. Since
  pingdotgg/t3code#28133 (same build) `inheritedOptions`, and an inherited selection, keep only
  options the model defines, so copying them into `target.options` is no longer refused. Since
  pingdotgg/t3code#22579 (same build) a queued child completion starts on the thread's current
  model instead of reverting it. Since pingdotgg/t3code#27836 (same build) a restart
  continuation tells the agent to confirm a state-changing action did not take effect before
  repeating it. Since pingdotgg/t3code#27468 (0.1.7-nightly.20261102.4061) a background command
  or Monitor the child left unawaited no longer holds its completion; awaited ones, background
  subagents and opaque background tasks still do. Since pingdotgg/t3code#28520 (0.1.7-nightly.20261102.4066)
  Stop and Force stop end a run whose provider turn had already finished, which used to stay
  `running` and hold every later message until a restart; `task_cancel` dispatches that Stop.
  Since pingdotgg/t3code#28516 (0.1.7-nightly.20261101.4035) a child's pending approval also shows
  in the parent thread for the user to answer, and in Full access Claude's dangerous-removal check
  rejects the command with its warning instead of asking; the agent uses a safe rewrite the
  warning supplies, or goes on without the removal and reports it (`docs/user/permission-modes.md`).
  Skills name only `git worktree remove`. Since pingdotgg/t3code#29842 (0.1.7-nightly.20261104.4151)
  `orchestrator_capabilities` reports a provider that is off for the caller's project as disabled,
  the check `delegate_task` already applied. Since pingdotgg/t3code#29909 (0.1.7-nightly.20261103.4119)
  a child's question steers into a busy parent's running turn when the provider steers without
  interrupting tools (Codex); a Claude parent still gets it queued behind the turn.
  Since pingdotgg/t3code#30257 (0.1.8-nightly.20261104.4179) the tool description ends "No secrets
  in `task`"; no skill or brief here puts one there. Since pingdotgg/t3code#27034
  (0.1.8-nightly.20261106.4247) Ultracode is a Claude on/off option of its own, and a
  `reasoningEffort: "ultracode"` in `target.options` reads as Extra High with it on
  (`withLegacyUltracodeEffort`); `agents/models.md` names no Ultracode. Since
  pingdotgg/t3code#28204 (0.1.8-nightly.20261105.4205) interrupting one child's completion wake
  keeps its siblings' wakes, and since pingdotgg/t3code#26435 (same build) an older pending
  question stays answerable. `t3_thread_send` takes `freshContext` (pingdotgg/t3code#30323), but
  a re-check is a new `delegate_task`, so no skill uses it. Since pingdotgg/t3code#32573
  (0.1.8-nightly.20261109.4392) a result read after the parent's run ended (a `mode: wait` call
  returning late) no longer marks the completion observed, so the idle parent still gets its wake;
  an in-turn read picks the calling provider's active run (`OrchestratorMcpService.ts`).
  Since pingdotgg/t3code#27753 (0.1.8-nightly.20261109.4429) `task_status` and a thread's
  `recentRuns` carry `executedModel`, the model the provider reported running (null when
  unknown; only the Claude adapter records it), and when it differs from the requested `model`
  the child's `summary` starts with "Requested model X; the provider reported running Y."
  (adopted as `reviewer-executed-model`, under Resolved). Since pingdotgg/t3code#33255 (same
  build) every thread `link` the MCP tools return carries the thread's title as its label; skills
  quote a link verbatim and parse none. Since pingdotgg/t3code#32504 (0.1.9-nightly.20261111.4515)
  a follow-up task whose child queues a run on its own thread settles on that run's reply, not on
  the turn that queued it (`delegatedTaskResultRun`), as the original task already did; since
  pingdotgg/t3code#32815 (0.1.9-nightly.20261110.4478) removing one queued completion keeps its
  siblings' wakes; since pingdotgg/t3code#33446 (0.1.9-nightly.20261111.4501) a send to a finished
  child from an MCP client with no thread scope (`t3 thread send`) wakes the parent too, a path no
  skill uses. Since pingdotgg/t3code#33295 (0.1.9-nightly.20261110.4478) a call reads only the
  caller's active runs and `task_status` reads the result from the child's records; the result
  fields are unchanged. `claude-fable-5-2` (pingdotgg/t3code#33500, 0.1.8-nightly.20261109.4433)
  was listed on 2026-11-11; `agents/models.md` names it nowhere. Since pingdotgg/t3code#35032
  (0.1.10-nightly.20261112.4580) a `mode: wait` call returns its task handle (`waitTimedOut`)
  after 4 minutes by default instead of 10, before Node fetch drops a silent call at 300 s; the
  skills here delegate with `mode: async`. Since #34489 (0.1.10-nightly.20261112.4564) Codex and
  Pi runs report `executedModel` too, so a Codex reviewer's model is no longer null. Since #26721
  (0.1.10-nightly.20261111.4544) every MCP tool rejects a top-level argument it does not declare
  ("Unknown argument"), where it used to drop it; every argument the skills and briefs name was
  in the tools' schemas on 2026-11-12. Since #33426 (0.1.10-nightly.20261112.4564) a model the
  catalog lacks is refused only after the provider's catalog is refreshed, and since #26625 an
  alias matches. A failed task keeps its child's final report as `summary` (#34915,
  0.1.10-nightly.20261112.4580); results survive the parent's wake turns (#34568, same build) and
  a steer during a `mode: wait` (#27387, 0.1.10-nightly.20261111.4544); cancelling a task whose
  child had only background work left reports `interrupted` (#21676).
  Source: `packages/contracts/src/orchestratorMcp.ts`. Read-only review
  is a prompt rule (`agents/reviewer.md`), not something T3 enforces.
- **Used by:** `agents/models.md` § Reaching each model; `skills/code-review/SKILL.md` § Spawning
  a reviewer; `agents/reviewer.md`; `agents/research.md`
- **Breaks if:** `summary` stops carrying the child's report, a child's question stops waking
  the parent (it would wait forever), `clientRequestId` stops
  deduplicating a retry, the `target` shape or live model ids change, or children stop sharing
  the parent's checkout by default.

### delegate-task-worktrees

- **Relies on:** a `delegate_task` child with `isolation: worktree` gets a checkout in T3's
  managed folder at the parent's local commit, on a branch of its own, with the project's setup
  run before it starts (uncommitted edits stay out; refused when the repo lacks that commit,
  pingdotgg/t3code#20213). T3 may rename that branch, so the child reads it rather than assume
  it. With `mode: async` the call returns at once with `next` ("Completion wakes this thread, so
  end your turn"), and the child's completion wakes the parent with its `summary`
  (`apps/server/src/mcp/toolkits/orchestrator/tools.ts`,
  `packages/contracts/src/orchestratorMcp.ts`). The result has no branch field, so the child's
  report names it. Tried 2026-10-26; the trial is under `implementer-worktrees`. Since
  pingdotgg/t3code#25700 (0.1.4-nightly.20261027.3796) several children launched at once no
  longer race on `.git/config.lock`, which could leave a branch without its worktree or a renamed
  branch the thread no longer matched; `implement-spec` § 2 launches them in parallel. Since
  pingdotgg/t3code#27221 (0.1.6-nightly.20261030.3904) a queue held by a provider failure, a
  restart or a Stop releases messages from agents, the server and scheduled tasks once the
  thread's newest run completes; a user's held messages still wait for that user. By that rule a
  child's completion held on the parent gets through (read from the PR, not tried here).
- **Used by:** `skills/implement-spec/SKILL.md` § 2, § 3, § Route change (`task_cancel`, under
  `delegate-task-reviews`) and § 4 step 3; `agents/implementer.md`;
  `agents/models.md` (Reaching each model); `skills/implement/THREADS.md` ("Work where you
  started")
- **Breaks if:** the checkout stops starting at the parent's local commit or skips setup, an
  async child's completion stops waking the parent, or storage cleanup starts removing a child's
  checkout before the orchestrator merged its branch.

### background-command-wait

- **Relies on:** a Bash command started with `run_in_background: true` keeps running across
  turns, and `t3_background_wait` with its task ID holds the turn until it exits; T3's injected
  instructions name it the way to wait for a background command (0.1.8-nightly.20261109.4399).
  Since pingdotgg/t3code#34343 (0.1.10-nightly.20261112.4564) the tool is marked read-only, so
  Claude's Plan mode runs it without asking.
- **Used by:** `skills/implement/HEAVY.md` § 3 (`gh run watch` on the § Heavy CI run)
- **Breaks if:** `t3_background_wait` goes away or stops returning when the command exits, so the
  session has to poll the run.

### background-subagents-keep-t3-tools

- **Relies on:** a Claude subagent started with the Agent tool runs in the background by default,
  and keeps calling T3 tools (the preview tools, `html_render`, `t3_thread_send`) with its
  parent thread's credential after the parent's turn ended, for as long as T3 lists it as a
  running background subagent of the same provider instance (pingdotgg/t3code#19751, since
  0.1.1-nightly.20261017.3238; `isLiveCallerShell` and `assertLiveCaller` in
  `apps/server/src/mcp/threadAccess.ts`, where `isLiveCallerShell` moved from
  `OrchestratorMcpService.ts` in 0.1.4-nightly.20261027.3796 unchanged). Before that build, such
  a call failed with `parent_not_active`. Still refused: `delegate_task`, `create_threads` and `request_secret`,
  and any call from a subagent that finished and was resumed by its own background task. After
  a restart, T3 now wakes a thread whose subagent's background work the restart cut
  (pingdotgg/t3code#19750). The mechanism is unchanged in 0.1.4-nightly.20261028.3822, but since
  0.1.3-nightly.20261025.3669 T3's injected instructions steer away from it
  (pingdotgg/t3code#24850, `orchestrationInstructions.ts`), and since pingdotgg/t3code#27139
  (0.1.7-nightly.20261102.4093) they say it outright: "Claude `Agent`, `run_in_background:false`
  ... Background agent: `delegate_task`, never a background `Agent`". The mechanism is unchanged
  in 0.1.8-nightly.20261104.4165 (`threadAccess.ts` changed only its imports). Since pingdotgg/t3code#30257
  (0.1.8-nightly.20261104.4179) `request_secret` takes a pasted `value` and saves it to a file with
  no card, but that path runs after the active-run check, so a background subagent is still
  refused. `implement-spec` moved its background implementers
  to `delegate_task` on 2026-10-26 (`implementer-worktrees`).
- **Used by:** `skills/implement/PREVIEW.md` § The loop step 1 (parallel subagents each open their
  own tab)
- **Breaks if:** T3 again ties a caller's tools to the parent's active run, so a background
  subagent's preview calls fail once the parent's turn ends.

### login-shell-path

- **Relies on:** T3, and the Claude Code and Codex sessions it starts, inherit PATH from the
  desktop login session, so a line in `~/.profile` reaches the agent's shell. Since
  pingdotgg/t3code#28556 (0.1.7-nightly.20261101.4035) the desktop starts on a cached PATH merged
  with the inherited one (`shell-environment-cache.json`), probes the login shell in the
  background and passes the result to the server, so a PATH change reaches only sessions started
  after that probe finishes (5 s timeout per shell;
  `apps/desktop/src/shell/DesktopShellEnvironment.ts`). A provider process started earlier keeps
  the PATH it started with until it restarts. Unchanged in 0.1.8-nightly.20261109.4399:
  pingdotgg/t3code#33153 only adds `awaitUserShellDiscovery`, which tells whether the user's own
  login shell or a fallback gave the PATH, for setting up the `t3` command. Since
  pingdotgg/t3code#35033 (0.1.10-nightly.20261112.4580) the first shell that times out at 5 s is
  read once more with 20 s, for a profile slow only while the machine boots.
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
  start a fresh thread on this repo's project, in its own T3 worktree from `origin/main` (since
  pingdotgg/t3code#27983, 0.1.7-nightly.20261101.4016, a task created or unbound over MCP gets
  `{baseRef: "origin/<default branch>", startFromOrigin: true}`, resolved once by
  `resolveScheduledTaskBaseRef` in `apps/server/src/mcp/OrchestratorMcpService.ts`; a task made
  before keeps its stored `{baseRef: "main"}`, which is this repo's default branch;
  `apps/server/src/scheduledTasks/ScheduledTaskService.ts`), and run a prompt
  that points at a skill here (since pingdotgg/t3code#25423, 0.1.3-nightly.20261027.3748,
  `schedule_task` with a `scheduledTaskId` also updates a task; `update_scheduled_task` is gone): "Weekly upstream review" on Mondays at 09:00
  (`skills/upstream-review/SKILL.md`), and "T3 update review" daily at 09:00
  (`skills/t3-update-review/SKILL.md`). Each opens its bookkeeping PR from that thread. "Weekly
  test audit" (`skills/test-audit/SKILL.md`) is the same kind of task made on each project that
  wants it, Mondays at 10:00, and opens its PR on that project. A task whose prompt calls the
  Skill tool needs a model-invoked skill: the tool refuses one with `disable-model-invocation`,
  and the task still shows `succeeded`. A prompt that opens the `SKILL.md` by path, as the two
  tasks on this repo do, works either way. Since
  pingdotgg/t3code#28474 (0.1.7-nightly.20261101.4035) an interrupt no longer leaves a task marked
  busy until a restart, which made scheduled polls skip it silently. A managed policy
  (pingdotgg/t3code#27197, `/etc/t3code/policy.json` on Linux) can block webhook tasks and cap
  runtime modes; this machine had none on 2026-11-02. Since pingdotgg/t3code#30326
  (0.1.8-nightly.20261106.4247) a task has a `threadMode`: `new_thread`, `continue` or
  `fresh_session` (`schedule_task`'s `freshSession`, also in its result). A task unbound before
  the migration stays `new_thread`, and a save that names no mode keeps the stored one, so both
  reviews still start a new thread per run. The one-time re-read `babysit-pr` schedules binds to
  its thread, so it is `continue`, as before. `fresh_session` would keep every run in one thread
  without its context, but a bound run uses that thread's checkout, never a fresh worktree from
  `origin/main`, so the reviews stay on new threads. Since pingdotgg/t3code#31379
  (0.1.8-nightly.20261108.4367) Settings → Scheduled tasks → Destination moves a one-thread task
  to another thread of its project, and a save that changes a task's thread refuses one deleted,
  archived or in another project; an unchanged destination is not rechecked. `babysit-pr`'s
  re-read binds to its own live thread, so it passes. Since pingdotgg/t3code#32494
  (0.1.9-nightly.20261111.4515) a `schedule_task` update recomputes the workspace strategy only
  when the task moves between bound and unbound, so `bindToCurrentThread: false` on a task already
  unbound keeps its stored strategy instead of resetting it to a fresh worktree; unbinding a bound
  task still switches it to one. Since pingdotgg/t3code#23609 (0.1.10-nightly.20261112.4564) a
  recurring task bound to a busy thread skips a slot while its previous occurrence is still
  queued there; the reviews are unbound, and `babysit-pr`'s re-read is `once`, so neither
  skips. A task outlives what made it: a `once` task that ran stays listed with `nextRunAt` null
  (`nextScheduledRunAt` in `apps/server/src/scheduledTasks/Schedule.ts`), `enabled: false` keeps
  the row, and a thread's bound tasks are deleted only with the thread
  (`deleteForThread`, reached only from `apps/server/src/orchestration-v2/ThreadDeletion.ts`), so
  `babysit-pr` deletes its re-read and `housekeeping` sweeps leftovers
  (`pr-watch-unreported-checks`). Since #34801 (0.1.10-nightly.20261112.4580) a `schedule_task`
  update applies `freshSession`, which it used to drop. A run's outcome now reaches `lastRunStatus`
  (`scheduled-run-status`, `scheduled-missed-runs`).
- **Used by:** `skills/upstream-review/SKILL.md` § Cadence; `skills/t3-update-review/SKILL.md`
  § Cadence; `skills/test-audit/SKILL.md` § Cadence; `skills/housekeeping/SKILL.md` (it removes
  only spent or orphaned `once` tasks, never these recurring ones)
- **Would improve if:** T3 deletes a `once` task after it runs, or deletes a thread's bound tasks
  when the thread is settled or archived.
- **Breaks if:** scheduled runs stop starting when no thread is open, stop getting a worktree of
  their own, the MCP default base stops following the project's default branch, or the scheduler
  drops `fixed_time` tasks. A task stored before that build on a project whose default branch
  is not `main` keeps the Base branch set in Settings → Scheduled tasks
  (pingdotgg/t3code#16183).

### fan-out-other-projects

- **Relies on:** `t3_project_list` returns every project with its `id`, `workspaceRoot` and
  `repositoryIdentity` (null for "No project"; else `canonicalKey`, the same for two entries of one
  repo). The list holds stale entries beside current ones (on 2026-11-11, `en-escena` at
  `~/projects/en-escena` beside `enescena` at `~/.t3/projects/enescena`, two repos with different
  keys). `t3_thread_launch` with another project's `projectId` and a `worktree`
  `workspaceStrategy` creates that project's checkout and runs its setup, which `delegate_task`
  refuses for a local `target.projectId` other than the parent's (`delegate-task-reviews`). The
  launch itself is `thread-launch-workspace`; a child's PR comes from `list_thread_pull_requests`
  (`pr-watch-is-native`). Since pingdotgg/t3code#35005 (0.1.10-nightly.20261112.4580) a project's
  identity follows `gh repo set-default`, and since #35080 (same build) an origin URL with a space
  gets one; since #29109 and #29187 (0.1.10-nightly.20261112.4564) `t3_thread_launch` and
  `t3_thread_list` say when the `projectId` names no project.
- **Used by:** `skills/fan-out/SKILL.md` §§ 1 and 3
- **Breaks if:** `repositoryIdentity.canonicalKey` or `workspaceRoot` leave the project list, or
  `t3_thread_launch` stops accepting a `projectId` other than the caller's.

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
  report, or a bookkeeping PR that never appeared, is a failed run. A run that starts right
  after the machine wakes can fire before the network is up: workspace preparation fails on
  `git fetch` ("Git could not reach the remote", `retryable: false`) and the task still says
  `succeeded` (all three Monday runs on 2026-10-19; again the daily review on 2026-11-04, retried
  by hand). Still so in 0.1.8-nightly.20261109.4399:
  `lastRunStatus` is `failed` only when the launch call itself fails, and since
  pingdotgg/t3code#29889 (0.1.7-nightly.20261104.4151) `lastRunError` is a plain message without a
  stack trace. `run_scheduled_task_now`
  now returns the thread its run went to (`null` when dispatch failed), so a manual run's thread
  is found from the call, and a refusal carries the scheduler's own reason ("Schedule task is
  already running."): the tool passes it through since pingdotgg/t3code#25647
  (0.1.7-nightly.20261101.4016), and the service stopped re-wrapping it since
  pingdotgg/t3code#29620 (0.1.7-nightly.20261104.4151).
- **Used by:** `skills/upstream-review/SKILL.md` § Cadence; `skills/t3-update-review/SKILL.md`
  § Cadence; `skills/test-audit/SKILL.md` § Cadence
- **Would improve if:** a run that fails or ends without its result is recorded as failed.
- **Partly met in:** 0.1.10-nightly.20261112.4580 (pingdotgg/t3code#34815; closes #30844, and
  #17889 closed with it). After a dispatch T3 follows the run for up to 24 hours, and a run that
  ends `failed`, `interrupted`, `cancelled` or `rolled_back` sets `lastRunStatus: failed`, with the
  provider's own failure as `lastRunError` or "The run failed." / "The run was stopped." / "The
  run was cancelled." / "The run was rolled back." A queued run cancelled by a steer into the
  active run is not a failure. Still `succeeded`: a run that completes without its report or PR,
  and one still running after 24 hours. A run whose workspace preparation fails on `git fetch`
  was not tried; whether it gets a run for T3 to follow is unread. So a run's thread stays the
  record of whether it did its work, and `failed` on the task is now a reliable sign that it did
  not. Both review skills' Cadence sections say so since 2026-11-12.
- **Watch:** PR pingdotgg/t3code#23131 (open: scheduled runs record how their turn ended); a
  completed run without its result has no issue of its own

### t3json-manual-import

- **Workaround:** each project's `t3.json` is imported once per T3 install (project settings →
  Actions → Import from t3.json); until then T3 runs no setup, in a thread's worktree or an
  implementer's checkout.
- **Used by:** `skills/implement/THREADS.md`; `agents/implementer.md` step 1
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
- **Partly met in:** 0.1.8-nightly.20261106.4247, untried. Cleanup keeps "Repository or branch
  changed" when the worktree's branch differs from the thread's recorded `branch`
  (`branchChanged` in `storageCleanup.ts`), and since pingdotgg/t3code#31599 that recorded branch
  follows the worktree once T3's VCS status cache sees the change (`renamed-branch-in-thread`).
  So a renamed worktree may now be judged by its new branch's PR. Not settled: the sync runs only
  when the status cache refreshes that worktree, and #17813 is still open. On 2026-11-06 this
  review's own thread switched its worktree to a new branch mid-turn: `t3_thread_read` gave the
  old branch until the turn ended, and the new one on the next turn, so the recorded branch does
  follow a switch. Cleanup removing such a worktree is still unseen. **Ready** once a
  worktree whose branch was renamed after the thread started is removed after its PR merges
  (Settings → Maintenance → Cleanup → Last run); then `housekeeping` drops its renamed-branch row.
- **Watch:** pingdotgg/t3code#17813 (open; #16559 closed as its duplicate on 2026-10-22), fixed by
  no open PR: #22805 (run finalization updates `thread.branch` to the checked-out branch) closed
  unmerged on 2026-10-30 at a maintainer's request, as the approved direction covers only a
  worktree belonging to exactly one thread; #11078
  (open; the sidebar keeps the creation-time branch name after a rename)

### storage-cleanup-stack-layers

- **Workaround:** `housekeeping` sweeps a worktree whose PR merged into another PR's branch, since
  T3 counts only merges into the default branch (`storageCleanupPullRequestMerged`).
- **Used by:** `skills/housekeeping/SKILL.md` (the stack-layer row)
- **Would improve if:** T3's merged-worktree cleanup accepts a PR merged into a stack parent.
- **Watch:** pingdotgg/t3code discussions/24108 (open; posted 2026-10-23 after #14758 closed
  `not_planned` with feature requests sent to Ideas); `storageCleanupPullRequestMerged` in
  `apps/server/src/storageCleanup.ts` (its `baseRef === defaultBranch` condition)

### storage-cleanup-orphan-folders

- **Workaround:** `housekeeping` removes a folder in T3's managed folder that no thread uses, once
  it holds no uncommitted work and its branch's PR is merged or closed. T3 lists such folders, with
  their sizes, under Settings → Maintenance → Last run (pingdotgg/t3code#19749), but never removes
  them, and the report has no MCP tool. `t3_worktree_list` cannot find them either: it lists
  git's branch refs and the checkout each one is in, with no thread and no detached worktree
  (seen on 2026-10-17), so an orphan on a branch is listed like any other. An orphan is a folder
  no live thread's `worktreePath` (from `t3_thread_read`) names. Since pingdotgg/t3code#25883
  (0.1.8-nightly.20261108.4353) the report also finds a project worktree nested deeper in a plain
  folder (`<repo>/replay/<n>`), from each project's `git worktree list`, and lists it as "No thread
  uses this worktree" instead of listing its holding folder; still not removed.
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

### rebuilt-worktree-no-setup

- **Workaround:** nothing may assume setup ran. T3 runs `runOnWorktreeCreate` only for a new
  worktree. Storage cleanup removes a worktree with its ignored files (on PR merge, or by
  `worktreeAfterDays`, `worktreeUnchanged` or `worktreeSettledAfterDays`), and on the thread's next
  turn `ProviderTurnStartService.recreateMissingWorktree` runs only `pruneWorktrees` and
  `createWorktree`. The rebuilt worktree has the tracked files and nothing setup or first use
  made: no linked env file, no project-local env override, usually no dependencies. So a project's
  scripts fail clearly when a file setup would have made is missing, rather than fall back, and
  new work on a merged thread goes in a new thread. Measured 2026-10-29 on 0.1.6-nightly (en-escena
  thread 464976f7-a2df-41b5-9a98-0ce1e7d1ff58): `~/.t3/userdata/logs/server.trace.ndjson` holds the
  warning "provider turn start recreating missing worktree" at 21:52:50 -03, then the
  `recreateMissingWorktree` and `GitVcsDriver.createWorktree` spans, with no setup span and no
  setup terminal log under `logs/terminals/`. `ProviderTurnStartService.ts` on T3's `main` has no
  reference to a setup script (keyword search of that file only; the same at
  0.1.7-nightly.20261102.4066, after pingdotgg/t3code#26758 changed which ref the recovery restores,
  at 0.1.8-nightly.20261109.4399, and at 0.1.9-nightly.20261111.4515, whose diff to the file
  leaves `recreateMissingWorktree` alone).
- **Used by:** `skills/implement/THREADS.md` (the intro); `skills/housekeeping/SKILL.md` (a live
  thread's resources are kept for its resume)
- **Would improve if:** T3 runs `runOnWorktreeCreate` when it recreates a worktree.
- **Watch:** `recreateMissingWorktree` in
  `apps/server/src/orchestration-v2/ProviderTurnStartService.ts`. No upstream issue filed: none
  covered this on 2026-10-30 (nearest: #26745 and PR #26758, the same recovery code, merged; #24390, a
  folder without `.git` is not rebuilt), and every confirmed case was a merged thread reopened,
  which is exceptional. File one if a live thread with unfinished work resumes bare.

### pr-watch-unreported-checks

- **Workaround:** `babysit-pr` reads the round on every wake and treats a required check not
  reported yet, a check still running or `mergeStateStatus` `UNKNOWN` as not ready. In T3 it ends
  the turn on the watch and waits on nothing else, as T3's runtime instructions require: "For PR
  waits, no sleep, loops, gh --watch, Monitor or ScheduleWakeup" (`runtimeInstructions.ts`;
  unscoped since pingdotgg/t3code#24850, scoped to PRs by pingdotgg/t3code#26681,
  0.1.6-nightly.20261031.3969). Where no wake will come it acts on the wake it has: a red check
  or an open finding goes to triage at once, so one push may not answer a whole round, and a
  required check unreported once every other check has finished is reported as BLOCKED. One gap
  stays: a required check that never reports while another still runs ends the turn, and no wake
  follows. That gap, and a wake the watch misses outright (rubens #79 and en-escena #1752, seen
  2026-11-02 and 2026-11-03: every check passed and no wake came), are covered by a one-time
  `schedule_task` (`{type: "once", runAt}`, bound to the thread by default), the **backstop**:
  `babysit-pr` makes one per PR on its first wait and moves it 20 minutes out (`schedule_task`
  with its `scheduledTaskId`) before each later turn it ends on the watch; its run re-reads the
  round (rubens #220, 2026-11-09: the watch missed a wake and the backstop's run merged it). T3
  never removes it by itself: a `once` task that ran stays listed with `nextRunAt` null
  (`nextRunAfterRun`; `nextScheduledRunAt` in `apps/server/src/scheduledTasks/Schedule.ts`),
  `enabled: false` keeps the row, and `ScheduledTaskService.deleteForThread`
  (`apps/server/src/scheduledTasks/ScheduledTaskService.ts`) runs only when its thread is deleted
  (`apps/server/src/orchestration-v2/ThreadDeletion.ts`, through the `scheduled-tasks.cleanup`
  effect and `ResourceCleanupService.cleanupScheduledTasks`), never when it is settled or
  archived. So `babysit-pr` § 5 deletes it with `delete_scheduled_task`, and `housekeeping` sweeps
  any left behind (over 14 days to 2026-11-12, 4 of 59 babysat sessions only disabled
  it, 4 more left it, and one thread made 7 by scheduling on every wait). Until
  pingdotgg/t3code#29450 (0.1.7-nightly.20261103.4106) a watch stopped for good after eight failed
  host reads, so a network outage ended it silently; it now keeps reading through `failed` host
  errors. That may explain the missed wakes above (not checked against their logs); the one-time
  re-read stays for the never-reporting check. Outside T3 the background
  `gh pr checks --watch` loop stays. Chosen by the user on 2026-11-01.
- **Used by:** `skills/babysit-pr/SKILL.md` § 2 (the T3 and outside-T3 waits and the state table)
  and § 5 (deleting the backstop); `skills/housekeeping/SKILL.md` (the scheduled-task sweep)
- **Would improve if:** `watch_pull_request` wakes the thread when a required check has not
  reported, and once every check has finished rather than only on a failure or on all required
  checks passing; then those two cases need no handling of their own. It would also improve if
  T3 deletes a `once` task after it runs, or deletes a thread's bound tasks when the thread is
  settled or archived; then neither the § 5 delete nor the housekeeping sweep is needed.
- **Partly met in:** 0.1.3-nightly.20261023.3566. T3 now wakes once the other checks finish after
  the required ones passed early (pingdotgg/t3code#23904), and once when a GitHub head has had no
  checks for 15 minutes or more (pingdotgg/t3code#23863; on time since #25437). Still no wake
  while a required check has not reported and others have, nor when the rest finish after a red
  check woke the thread. Since pingdotgg/t3code#34624 (0.1.10-nightly.20261112.4564) a workflow run
  still queued with no jobs counts as pending, so a skipped advisory check no longer wakes "checks
  passed" before CI starts; a required check GitHub has not created yet is PR #28200's (open).
- **Watch:** pingdotgg/t3code#28200 (open: PR watches wait for required checks that have not
  started yet); discussions/18047 (open); discussions/23245 (open; #16924, converted
  2026-10-22); #17831 (closed without merging on 2026-10-14)

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
- **Watch:** pingdotgg/t3code discussions/23305 (open; #17703, converted 2026-10-22)

### deb-update-relaunch-no-new-privs

- **Workaround:** on a `.deb` install, an in-app restart (after an update, or after a setting
  that relaunches: server exposure, Tailscale Serve, local environment, WSL) uses Electron's
  `app.relaunch()`, which sets `no_new_privs` on the new process. Its next "Restart to install"
  can't run `pkexec` ("pkexec must be setuid root", exit 127): no password prompt, the backends
  restart, nothing installs. So before installing an update, quit T3 and open it from the
  desktop. Check with `grep NoNewPrivs /proc/$(pgrep -o -x t3code)/status` (`1` = will fail).
  Seen 2026-10-29, 0.1.4-nightly.20261028.3841 → 0.1.5-nightly.20261029.3873. Still so on
  2026-11-02: the running 0.1.7-nightly.20261102.4066 has the flag at `1`.
- **Used by:** no skill; the user's update routine on the Linux machine.
- **Would improve if:** a Linux relaunch no longer sets `no_new_privs`. Adopting means: install
  the fixed build from a desktop-launched instance, reopen once more (the old code did that
  restart), then check that the next update installs from the in-app restart with the flag at
  `0`, and report the result on pingdotgg/t3code#14905.
- **Watch:** pingdotgg/t3code#14905 (open), with no open fix: PR #15387 closed unmerged as stale
  (open over three weeks), as did its follow-up #35173 and #27884 (keep sudo working in terminals
  after a Linux relaunch); checked 2026-11-12

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
  Rubens' PRD #16 run on 2026-10-27 (desktop 0.1.4-nightly.20261027.3783) met three faults,
  each worked around in `PREVIEW.md`: a tab the preview pane does not show runs no
  `requestAnimationFrame`, so clicks time out waiting for stable frames (with `open: true` too);
  after `preview_resize` to 1440×900 the response always said 1280x800 and the page laid out at
  either width; and mid-session captures came out blurred on a page with no CSS filters, where
  `playwright-cli` took the same screens sharp at 1440×900. pingdotgg/t3code#22877
  (0.1.4-nightly.20261027.3796) may explain the resize fault: when the desktop attached its page
  more than 10 s late, the agent drove a headless page while the panel showed another; now the
  panel streams the server's page. Rubens' drives on 2026-10-27 to 2026-10-29 (PRs #20, #29, #36,
  #43, #53) answer part of it. The 1280×800 report was the capture cap: Spec 16 later read
  `innerWidth` 1440 the whole time. One thread still saw the layout flip ("1280 px after a resize
  to 1440, then 1440 after a resize to 1280", #36), so `preview_resize` is still unsettled. Snapshot
  timeouts became the blocker. "Later snapshots timed out every time" (#43), and #53 found them
  "still timing out, even with the tab shown", which leaves the snapshot-paints-a-frame workaround
  nothing to work with. A fresh tab cleared it once (#20). #36 and #53 took every capture with
  `playwright-cli`. Smaller gaps, now in `PREVIEW.md` step 4: `type` appends to a filled field;
  a date input takes only ISO text (the browser's locale is en-US); `press Tab` moves no focus; a
  loose CSS selector (`main button`) caught the wrong button. Since pingdotgg/t3code#28027
  (0.1.7-nightly.20261101.4035) `preview_open` also takes the dev-server `target`
  of `preview_navigate`, which wins over `url`; `PREVIEW.md`'s URL still works. Since
  pingdotgg/t3code#23489 (0.1.7-nightly.20261103.4119) a timed-out click names its target and
  says "The click may have happened; check the page before retrying", with whether the target
  still matches (`namedTargetTimeout` in `ServerBrowserPage.ts`), so some of the trial's lost
  clicks may have been dispatched clicks whose wait timed out. A failed `preview_open` no longer
  leaves a hidden tab (pingdotgg/t3code#29865, #29885). Snapshot capture is unchanged through
  0.1.8-nightly.20261107.4314 (`ServerBrowserPage.ts` only moved its errors to a tagged class), so
  no snapshot fault moved. Since pingdotgg/t3code#30306 (same build) the server's headless browser
  closes after five idle minutes, and the next agent tab starts it cold (about 190 ms); since
  pingdotgg/t3code#24186 (0.1.8-nightly.20261105.4205) idle agent tabs free a slot when the
  32-tab limit is full. Since pingdotgg/t3code#28255 (0.1.8-nightly.20261108.4353)
  `preview_snapshot` with `save: true` also keeps the uncapped capture and writes that to disk;
  the agent's image stays 1280 px wide, and capture and timing are unchanged. Since
  pingdotgg/t3code#32861 (0.1.9-nightly.20261110.4478; closes #32848) a fresh desktop tab is
  announced only once its first page is up: before, 11 of 30 new `about:blank` tabs (16 of 30
  under load) lost every `preview_wait_for`, locator `preview_act` and `preview_snapshot` for
  good while `preview_evaluate` still worked, which matches the trial's lost clicks and the
  agent's turn to `preview_evaluate` from rubens #72 on (not checked against their logs). Since
  pingdotgg/t3code#23589 (0.1.9-nightly.20261110.4452) a tab the desktop shows reads
  `visible: true` and is the default for a call without `tabId`; since pingdotgg/t3code#33745
  (0.1.9-nightly.20261111.4515) a snapshot of a page with a large accessibility tree keeps 2,000
  characters of `visibleText` instead of none; since pingdotgg/t3code#31925
  (0.1.9-nightly.20261110.4465) `preview_evaluate` accepts top-level `await`. `t3_preview_close`,
  `PREVIEW.md` step 7's close, is unchanged. Since pingdotgg/t3code#24829
  (0.1.10-nightly.20261112.4564; closes #24812) desktop snapshots work again after the CDP relay
  reconnects. #23936 stays open, so **Retry when** is still not met. In the same builds: a
  locator that matches several elements is reported as ambiguous, no longer as an invalid
  selector (#34205); `preview_wait_for` stops at its timeout when the page stops answering
  (#32846); `preview_open` reports a tab it shows as visible (#26055); a desktop tab detached
  during setup no longer blocks later tabs (#34252); `preview_evaluate` always returns by value
  (#22948); and a recording keeps the page's last state (#33931) and stays decodable after a
  resize (#10495). Since 0.1.6-nightly.20261030.3904
  the preview browser runs in an agent scope, with the agents' +800 OOM score, low CPU weight and
  memory limits (pingdotgg/t3code#27239, #27176): "under agent memory pressure the preview
  browser is throttled too". Whether that bears on the snapshot timeouts is untested; a preview
  run's notes on memory pressure would settle it.
- **Used by:** `skills/implement/PREVIEW.md`; `skills/implement/SKILL.md` § 4; `contract.md`
  (the `verification.md` row)
- **Would improve if:** both hold, in the installed T3: a snapshot renders `backdrop-filter`
  correctly at a desktop viewport (pingdotgg/t3code#20899), and it saves at the viewport's size
  or the user accepts images 1280 px wide; and Rubens' three faults are gone (a hidden tab draws
  frames, `preview_resize` holds and reports the width the page gets, captures stay sharp). A fix to #20899 alone leaves this entry
  **watching** while the cap stands; ask the user about the 1280 px images. **Ready** only once
  en-escena's dialog probe passes (`/administracion/resultados`, Acciones → Descargar,
  1440×900). Adoption is then two steps: first each project's § Evidence
  takes its images with `preview_snapshot`, keeping the browser CLI installed; once ten PRs
  verified that way had no lost click, each `verification.md` drops the browser CLI and its
  install, and this entry is resolved.
- **Partly met in:** 0.1.3-nightly.20261026.3717. pingdotgg/t3code#24618 (closes #20899)
  captures at full scale and shrinks the finished PNG in the page, since Chromium "mirrors the
  top-left of the page into a `backdrop-filter` in any capture it shrinks"
  (`shrinkPng` in `ServerBrowserPage.ts`). The 1280 px cap stands (`MAX_SCREENSHOT_WIDTH`), so
  en-escena's dialog probe remains: the user accepted images 1280 px wide on 2026-10-26. The same build's injected
  instructions add a hurdle (pingdotgg/t3code#24850): "Never use `preview_*` to verify or show
  your own edit, even a frontend edit ... Use them only when the current request asks for browser
  work", and the browser section dropped its exception for "a skill or documented repository
  workflow that names one". Since 2026-10-26 `PREVIEW.md` says why its use is asked for: step 4
  and the project's `verification.md` require the drive. Since pingdotgg/t3code#26503
  (0.1.6-nightly.20261031.3969) the rule reads "Never use `preview_*` unasked to verify or show your own
  edit. Use them when the current request asks for browser work, including recording edits", the
  reading `PREVIEW.md` already gives it.
- **Probe:** passed 2026-10-26 in en-escena (`/administracion/resultados`, Acciones → Descargar
  resultados, 1440×900, demo data): the `preview_snapshot` capture, saved at 1280×800, shows the
  dialog's `backdrop-filter: blur(4px)` as an even blur with no tiles, matching a `playwright-cli`
  reference at 1440×900, and the dialog is legible. No capture mid-animation, no viewport drift.
  Faults seen: a role-locator click timed out twice on a visible button ("Ingresar", "Acciones")
  where an `aria-ref` or coordinate click worked; a background tab (`open: false`) drew no focus
  ring; `preview_resize` reports the capture size (1280×800), not the page's.
- **Tools renamed:** since 0.1.3-nightly.20261027.3748 one `preview_act` tool takes `action`
  (`click`, `type`, `hover`, `select`, `drag`, `upload`, `press`, `scroll`) and that action's
  fields, replacing the eight tools of those names (pingdotgg/t3code#25423).
- **Trial result:** decided by the user on 2026-11-02: the browser CLI clicks and takes the
  evidence, and `PREVIEW.md` covers a look at a page and a project whose § Drive names no CLI. Step
  one of **Would improve if** ran from 2026-10-26 and is undone. Counted from T3's store for
  2026-10-26 to 2026-11-02, every project: 28 of 125 `preview_act` clicks and 23 of 213
  `preview_snapshot` calls failed. Eleven merged PRs in en-escena, rubens and enescena took
  captures with `preview_snapshot`: rubens #20, #29, #43, #69, #72, #73, #74, #75, #76, #81, #83.
  None counts toward step two: #20, #29, #43, #69, #72 and #83 lost clicks; #74 and #76 had
  timed-out snapshots; #75 and #76 report blurred captures; #73 and #81 made no `preview_act` click.
  From #72 on the agent clicked through `preview_evaluate` instead (61 calls with a JavaScript
  click, a dispatched event or a `fetch`, #72 to #83), which skips what a real click checks. Clicks
  failed 23 of 81 times in `open: false` tabs and 3 of 40 in `open: true` ones, unevenly spread
  across threads; snapshots failed 14 of 131 and 9 of 63, so the tab's state does not explain them.
- **Retry when:** #23936 and #24812 are fixed, or #25862 merges. Then one real drive with
  `preview_act` clicks on the current build decides whether step one runs again. A PR counts toward
  step two only with real `preview_act` clicks, none lost, no timed-out snapshot and sharp captures.
- **Watch:** pingdotgg/t3code#23936 (open: `preview_snapshot` always times out on `open: false`
  tabs and in delegated children); #24812 (closed 2026-11-12 by #24829: snapshots timed out
  after the CDP relay reconnected); #25862 (open: bounds a stalled screenshot capture; it replaced #23515, closed
  unmerged 2026-11-10); #24130 (open:
  reports the actual snapshot timeout); #20899 (the blur, fixed; no issue asks to lift the size
  cap, and #10141, which tried, closed unmerged); `apps/server/src/preview/ServerBrowserPage.ts`
  (`MAX_SCREENSHOT_WIDTH`, `captureViewport`); `apps/server/src/mcp/toolkits/preview/tools.ts`;
  the trial's notes in the final reports of en-escena's and rubens' PRs

### remote-child-files

- **Workaround:** a reply's image renders from a path on the machine the thread runs on. A child
  delegated to a linked environment (`target.environmentId`) saves its captures on that machine,
  so the same path shows "Image unavailable" in the parent's thread (rubens #105's browser check
  on 2026-11-03). The parent copies each file to its own machine first, with the access the
  user's instructions give for that machine, and lists the path when it has none. No T3 tool
  reads or moves a file between environments (0.1.7-nightly.20261103.4138):
  `t3_attachment_prepare_upload` uploads to the caller's own server, and
  `t3_thread_send_attachments` sends to a thread there.
- **Used by:** `skills/implement/SKILL.md` § 7
- **Would improve if:** T3 renders a remote child's file in the parent's thread, or a tool fetches a
  file from a linked environment; then the copy step goes away.
- **Watch:** no upstream issue yet; check each update's MCP tool list for a cross-environment file
  tool

## Ready

None.

## Resolved

### scheduled-missed-runs

- **Workaround:** a `fixed_time` run that falls due while T3 is not running is dropped. When T3
  comes back more than 10 minutes past the due time, the scheduler moves the task to its next
  slot without running it (`MISSED_FIXED_TIME_GRACE_MS` in
  `apps/server/src/scheduledTasks/Schedule.ts`, `rescheduleMissedRun` in
  `ScheduledTaskService.ts`). Only a server log line records the skip: no thread, and the task's
  `lastRunStatus`, `lastRunAt` and run count stay at the previous run's. So a scheduled day with
  no run thread is a missed run, and the next run, or a manual one, covers it. Seen on
  2026-10-18: T3 was down from 03:45 to 14:17 UTC, and the daily review due at 12:00 never ran.
  Only `fixed_time` drops a run: `isMissedFixedTimeRun` is false for every other type, so an
  `interval` task and a `{type: "once", runAt}` task (pingdotgg/t3code#28104,
  0.1.7-nightly.20261101.4016) run when T3 is back. An interval has no fixed clock time, so the daily
  and weekly reviews stay on `fixed_time`.
- **Used by:** `skills/upstream-review/SKILL.md` § Cadence; `skills/t3-update-review/SKILL.md`
  § Cadence; `skills/test-audit/SKILL.md` § Cadence
- **Would improve if:** a missed run is run once on startup (catch-up), or is recorded on the
  task as missed.
- **Met in:** 0.1.10-nightly.20261112.4580 (pingdotgg/t3code#34815): a missed slot now sets the
  task's `lastRunStatus` to `failed`, with `lastRunError` "Missed a scheduled run because the
  server was not running at that time." (`rescheduleMissedRun` in `ScheduledTaskService.ts`).
  Still no catch-up run, no thread, and `lastRunAt` and the run count keep the previous run's.
  The update only lands while the row still holds the slot it read, so a run or an edit since
  wins.
- **Adopted:** 2026-11-12, by the user's call: both Cadence sections
  (`skills/t3-update-review/SKILL.md`, `skills/upstream-review/SKILL.md`) say `lastRunStatus`
  turns `failed`, with `lastRunError` saying why, for a run that failed, was stopped or was
  missed while T3 was down, and that `succeeded` only means the run started.
- **Watch:** `apps/server/src/scheduledTasks/Schedule.ts`, for a catch-up run

### lost-context-watch-state

- **Workaround:** a turn that starts without its context rebuilds the goal, branch and PR from
  `t3_thread_read` ("A lost context is recovered from T3" in `skills/implement/THREADS.md`), but
  cannot tell whether it was babysitting a PR: it reads the round again and may call
  `watch_pull_request` on a PR already watched, or end its turn without one.
- **Used by:** `skills/implement/THREADS.md` ("A lost context is recovered from T3")
- **Would improve if:** a thread read says which of its PRs it watches.
- **Met in:** 0.1.10-nightly.20261112.4580 (pingdotgg/t3code#34895): each open PR in
  `t3_thread_read`'s first page and in `t3_thread_list` carries `watching` and `watchStartedAt`
  (`OrchestratorMcpThreadPullRequest` in `packages/contracts/src/orchestratorMcp.ts`).
- **Adopted:** 2026-11-12, by the user's call: "A lost context is recovered from T3" in
  `THREADS.md` reads the open PRs from `pullRequests` and the rest from
  `list_thread_pull_requests`, and takes `watching: true` as a babysit to pick up at its read of
  the round, ending the turn on the running watch. `babysit-pr` is unchanged: the recovery hands
  the session to it.

### reviewer-executed-model

- **Workaround:** a review report names the model a reviewer ran on from the model the skill
  asked for (`agents/models.md` table), so a provider that runs another model (an organization
  that allows only Sonnet runs an Opus request on Sonnet) yields an "Opus review" Sonnet did.
- **Used by:** `agents/models.md` (a task on another model, and a fallback: "the report names
  the model and why"); `skills/code-review/SKILL.md` § Spawning a reviewer
- **Would improve if:** `delegate_task` reports the model that actually ran.
- **Met in:** 0.1.8-nightly.20261109.4429 (pingdotgg/t3code#27753): `task_status` gains
  `executedModel` ("Model the provider reported running, or null when unavailable. Can differ
  from the requested `model`", `packages/contracts/src/orchestratorMcp.ts`), taken from the run
  that produced the result, and a differing child's result starts "Requested model X; the
  provider reported running Y." Only the Claude adapter recorded it, so a Codex child read null
  until pingdotgg/t3code#34489 (0.1.10-nightly.20261112.4564), which records it for Codex and Pi.
- **Adopted:** 2026-11-10, by the user's call: `agents/models.md` § The rule has the report name
  the model that ran, from `executedModel` or the result's opening note, and count the review by
  that model's tier and family; null keeps the requested model.

### browser-setup-sudo-secret

- **Workaround:** when `preview_open` is refused because the host blocks the browser's sandbox
  (the error names `sudo ~/.t3/bin/t3 browser setup`), `PREVIEW.md` hands the fix to the user and
  finishes with § Drive's fallback, since an agent could not type a sudo password.
- **Used by:** `skills/implement/PREVIEW.md` (the refusal paragraph before § The loop)
- **Would improve if:** an agent can run a sudo command with a password only the user gives,
  without the password entering the chat.
- **Met in:** 0.1.8-nightly.20261109.4399 (pingdotgg/t3code#27748). T3's injected instructions now
  say: "A login, token, PIN, pairing code or sudo password only the user can give: call
  `request_secret` ... Sudo: if `sudo -n <cmd>` says a password is required, use
  `delivery: "file"` and run `sudo -S -p '' <cmd> < "$file"`" (`orchestrationInstructions.ts`).
  The setup is one-time per machine, done here since 2026-10-16, so it bears mainly on a new
  machine.
- **Adopted:** 2026-11-09, by the user's call; `PREVIEW.md` keeps "Agent browser access" as the
  user's setting, and for the sandbox refusal runs `t3 browser setup` through `request_secret`
  (`delivery: "file"`) once, then retries `preview_open`. A background subagent, which
  `request_secret` refuses (`background-subagents-keep-t3-tools`), hands the refusal to its
  parent.

### implementer-worktrees

- **Workaround:** `implement-spec` ran each implementer as a background Agent-tool worktree
  under `.claude/worktrees/`, set up by hand, an exception to `THREADS.md`'s "never create a
  worktree of your own".
- **Would improve if:** a `delegate_task` child with `isolation: worktree` (a checkout of the
  parent's local commit, with project setup done before the child starts) can commit to its own
  named branch that the orchestrator merges. Its result has no branch field today
  (`OrchestratorMcpDelegateTaskResult` in `packages/contracts/src/orchestratorMcp.ts`). Not tried
  yet: needs a trial. Since pingdotgg/t3code#20213 such a call is refused when the project's repo
  lacks the parent checkout's commit. Since 0.1.3-nightly.20261025.3669 T3 points agents at it:
  the `delegate_task` description says "Separate checkout or PR per child:
  `isolation:'worktree'`", and the injected instructions say "Never make a child's checkout in the
  shell or in `task`" (pingdotgg/t3code#24850), which this workaround does in
  `agents/implementer.md` step 2. Tried 2026-10-26 (a Sonnet child, `role: test`): the child got
  a checkout in T3's managed folder at the parent's local commit, made and committed to a branch
  of its own name, and that branch was a fast-forward of the parent's from the parent's worktree;
  the result still carries no branch field, so the report names it, as an implementer's does now.
  One catch: T3 had renamed the child's branch (`t3/<id>` to `t3/<slug>`), and a child that
  switches away from it is one storage cleanup keeps (`storage-cleanup-renamed-branches`), so the
  child commits on the branch T3 gave it.
- **Met in:** 0.1.3-nightly.20261026.3717, by the trial above.
- **Adopted:** 2026-10-26; `implement-spec` § 2 spawns each implementer with `delegate_task`
  (`isolation: worktree`, `mode: async`), a new attempt carries its earlier branch instead of a
  `SendMessage`, the brief dropped its setup step and commits on the branch T3 gave it, the
  harness wrappers went, and `THREADS.md` lost its exception. Relied on since as
  `delegate-task-worktrees`.

### pr-auto-link

- **Workaround:** the session calls `link_pull_request` right after `gh pr create`.
- **Used by:** `skills/implement/THREADS.md` ("One thread, one branch, one PR");
  `skills/implement/SKILL.md` § 7; `skills/implement-spec/SKILL.md` § 3 step 3
- **Met in:** 0.1.3-nightly.20261025.3669 (pingdotgg/t3code#24813). Once a shell command settles
  that runs `gh pr create` (or `glab mr create`) at a command position and prints the PR URL on a
  line of its own, T3 links that PR to the thread that ran it, with source `created`; a repeat
  settlement is a no-op and never relinks a PR the user unlinked. Nothing is linked for a `for`
  loop that creates several PRs, a `gh api` create, or output with more PR URLs than create
  commands. The tool copy dropped "Register every pull request you open" (pingdotgg/t3code#24850).
  Tried 2026-10-26 on this review's own PR (#28): `gh pr create`, run as the last of several
  shell commands, was linked with source `created` before any call, and `link_pull_request`
  afterwards returned `alreadyLinked: true`.
- **Adopted:** 2026-10-26; `THREADS.md` ("One thread, one branch, one PR") says T3 links a PR
  `gh pr create` opens, and keeps `link_pull_request` for a PR opened another way or missing from
  `t3_thread_read`'s `pullRequests`; `implement` § 7, `implement-spec` § 3 step 3 and
  `t3-update-review` step 10 point at it.

### storage-cleanup-archived-threads

- **Workaround:** `housekeeping` swept an archived thread's worktree once its PR was merged or
  closed and its tree was clean; deleting the thread also handed it to T3 (`worktreeOnDelete`).
- **Met in:** 0.1.2-nightly.20261021.3473 (pingdotgg/t3code#16473, `034b506`, shipped in
  0.1.1-nightly.20261020.3386; closes #17811). Cleanup judges an archived thread's worktree by the
  same merge, settle and age rules as a live one's, and an archived sharer keeps it.
- **Adopted:** 2026-10-23; the archived-thread row left `housekeeping`'s table, and its first row
  gives T3 a merged or deleted thread's worktree, archived or not. Part of
  `storage-cleanup-removes-thread-worktrees` since.

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
