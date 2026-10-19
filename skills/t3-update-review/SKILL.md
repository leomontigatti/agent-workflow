---
name: t3-update-review
description: "After a T3 Code update, check what changed against the T3 dependency files (the shared skills' and each project's): what it fixes, improves, changes or breaks in our workflows. Use when T3 was updated, when the scheduled update review runs, or when asked whether a T3 release affects us."
---

T3 Code ships nightly builds, several a day. What our workflows assume about T3 is written in two kinds of file (statuses: **active**, **watching**, **ready**, **resolved**; each file explains them): the root `t3-dependencies.md` of the shared-workflow repo, for what the shared skills, agents and hooks assume, and each project's `docs/agents/t3-dependencies.md`, for what only that project assumes. This review checks every build since the last reviewed one against all of them and reports what to do.

The review writes down what it learns and proposes what to change. What it learns is evidence: a status that moved, a new **watching** or **ready** entry, a T3 PR quoted under an entry. That goes straight into the shared `t3-dependencies.md`, in one bookkeeping PR the review opens (step 10), so a finding outlives the report and the next run starts from it. A change to a skill, a brief, a hook or a project file is only proposed: the user picks what to adopt, and that goes through the repo's normal workflow (worktree thread, branch, PR). A change to a shared skill reaches every project at once, so a finding about one is proposed once, against the shared-workflow repo. A finding about a project's own file is proposed for that project; the review edits no project.

## Steps

1. **Installed version.** Call the T3 `t3_environment_read` tool and take `serverVersion`. (From a shell: `~/.t3/bin/t3 --version`.)

2. **Collect changes.** Run:

   ```
   python3 -I <this-skill-dir>/scripts/changes.py <serverVersion>
   ```

   It reads the last reviewed version from `~/.local/state/t3-update-review/state.json`, and writes to `~/.local/state/t3-update-review/work/`: `release-items.md` (every PR in the releases between, deduplicated) and `watched.diff` (diffs of the T3 source our workflows depend on: MCP toolkits, orchestration instructions, storage cleanup, worktree setup, `t3.json` schema).
   - `UP TO DATE` → reply with one line ("T3 <version>: already reviewed") and stop.
   - `MISSING <path>` → T3 moved a watched file; find its new location and fix `WATCHED_PATHS` in the script, and say so in the report.
   - A dependency file that cites T3 source (`apps/…`, `packages/…`, `docs/…` in pingdotgg/t3code) not in `WATCHED_PATHS` → add it to the script, so the next run diffs it.

3. **Load the dependency files.** First the shared one: in the shared-workflow repo (the checkout `~/.agents/workflow` links to), `git fetch` and read `git show origin/<default>:t3-dependencies.md`. Then list projects with the T3 `t3_project_list` tool. For each one with a git repo other than the shared-workflow repo, `git fetch` and read `docs/agents/t3-dependencies.md` from the remote default branch (`git show origin/<default>:docs/agents/t3-dependencies.md`), never from the working tree, and never check anything out. When the default branch lacks it, look for it on an open PR's head branch (`git log --all -1 --format=%D -- docs/agents/t3-dependencies.md`), review against that copy, and say in the report it's pending merge on that branch. A project with the file nowhere goes in the report as "not covered".

4. **Drift check.** For each entry, confirm every file and heading under **Used by** still exists on the default branch of its repo and still says what the entry claims. Then grep for T3-specific rules (`t3`, `worktree`, `thread`, `mcp__t3`, T3 tool names) that no entry covers: in the shared-workflow repo's `skills/`, `agents/` and `hooks/`, against the shared file; in each project's `AGENTS.md`, `docs/agents/`, `.agents/` and `t3.json`, against the shared file and the project's together. A project entry that restates a shared one is drift too. All of it goes in the report as **drift**.

5. **Watched entries.** For each **watching** entry with a `Watch:` issue or PR: `gh issue view` / `gh pr view` on `pingdotgg/t3code`, following an issue's timeline (`gh api repos/pingdotgg/t3code/issues/N/timeline`) to the PR that fixed it. A merged fix is in the installed build when `gh api repos/pingdotgg/t3code/compare/<mergeSha>...<installedSha> -q .status` prints `ahead` or `identical`. Then the entry is **ready**: say what adopting it means.

6. **Reactive pass.** Triage `release-items.md`: drop items that can't touch our workflows (mobile, marketing, purely visual web fixes, providers we don't use) and keep anything about server, orchestration, MCP tools, threads, worktrees, pull requests, source control, storage, settings, project scripts, skills, and the Claude provider. Read `watched.diff` in full. Check each kept change against every entry's **Relies on**, **Breaks if** and **Would improve if**. With more than ~150 kept items, split them across parallel subagents in the **Miners** role of `~/.agents/workflow/agents/models.md`, each given the dependency files and a slice.

7. **Proactive pass**, only when `watched.diff` is non-empty or kept items add or change a T3 capability: for each workflow and skill the dependency files cite, ask whether the new capability makes it better, faster or cheaper. Each yes becomes a proposed new **watching** or **ready** entry, with evidence. A shared skill has one copy: report a finding about it once. A project-only skill or doc is checked in its own project.

8. **Report.** Write `~/.local/state/t3-update-review/reports/<YYYY-MM-DD>-<serverVersion>.md` and reply with its contents:

   ```
   # T3 update review: <since> → <installed> (<n> releases)

   ## Needs you             (what only the user can do: a T3 setting, a button in the app,
                            a decision on a ready entry; first, so it is read)
   ## Breaks / changes      (an active entry no longer holds; act first)
   ## Fixes / ready         (a watching entry's condition is now met)
   ## Improves              (new capability we could adopt; proposed entries)
   ## Drift                 (entries out of sync with the repo; uncovered rules)
   ## Not covered           (projects without a dependency file)
   ## Still ready           (every ready entry not adopted yet, one line each)
   ```

   Each finding: the file it is about (`shared`, or the project), the entry id, the T3 PR(s) with links, the evidence (a quote from the diff or release item), and the proposed edit: to the dependency file (status change, new entry) and to the workflow or skill itself. Leave a section out when it is empty; when every section is empty, the report is one line saying nothing affects us. **Still ready** comes from the dependency files' Ready sections, not from earlier reports: an entry stays there until it is adopted or the user declines it, so nothing proposed is lost between runs.

9. **Mark reviewed**, only after the report is written:

   ```
   python3 -I <this-skill-dir>/scripts/changes.py <serverVersion> --mark
   ```

10. **Bookkeeping PR**, when the report changes anything in the shared `t3-dependencies.md`. In a thread on the shared-workflow repo, on a `docs/t3-<serverVersion>` branch from the default branch, write the evidence, status moves and new entries the report gives for the shared file, run the lint (`python3 -I tests/lint_skills.py`), and open a PR whose body is the report. Link it to the thread with `link_pull_request`. Proposed edits to skills and projects stay in the body as proposals, never in the diff. The user's merge accepts the bookkeeping; their edits to it are final.

## Cadence

Daily: the T3 scheduled task "T3 update review" runs it at 09:00 in a fresh thread on the shared-workflow repo. Nightlies land several times a day, and a run with nothing new costs one version check. A run's thread is its only record: the task's `lastRunStatus` says `succeeded` whatever the run did, so a thread with no report is a failed run, and a scheduled day with no thread is a run T3 skipped because it was down at the time.
