---
name: fan-out
description: "Fan one change out across several projects: pick the projects, fix the shared wording, launch one thread per project, track their PRs."
disable-model-invocation: true
---

# Fan out a change

The argument is a change that has to land in several projects: most often a breaking
`contract.md` change from an agent-workflow PR, whose body names the projects and what each must
add or rename. This thread is the **coordinator**: it writes no project's code. Each project gets
its own thread, in its own worktree, running its own contract through `implement`, and opens its
own PR. The coordinator owns the list, the shared wording and the report.

## 1. Scope

Discover the projects; keep no index of them. List them with `t3_project_list`, then:

- skip an entry whose `repositoryIdentity` is null ("No project", scratch);
- keep one entry per `repositoryIdentity.canonicalKey`, preferring the one whose `workspaceRoot`
  is under `~/.t3/projects/`. Two entries with similar titles and different keys are two repos;
- leave out the coordinator's own project: its change is the shared PR, not a child.

For each project left, `git fetch` and read the top of `AGENTS.md` on its remote default branch
(`git show origin/<default>:AGENTS.md`), plus whatever the change touches there (a contract file,
a skill it renames). Mark it **in** or **out**, with a one-line reason. Show the user the list and
wait for their agreement.

Done when every project is in or out with a reason and the user has agreed to the list.

## 2. Fix the shared parts

Write `/tmp/fan-out-<slug>/notes.md`, outside every repo:

- the change, and the PR or issue it comes from;
- one section per **in** project: what that project must do;
- every name, heading, wording and file path that must be identical in every project, spelled
  out exactly once.

The notes are the single source of truth for what is shared, so the children stay in step. A
question a child raises about shared wording is answered in the notes, then pointed at.

## 3. Launch one thread per project

`delegate_task` refuses a local `target.projectId` other than the parent's, so each child is a
top-level thread: `t3_thread_launch` with

- `projectId`: the project's id from step 1;
- `workspaceStrategy`: `{type: "worktree", baseRef: "origin/<default>", startFromOrigin: true}`;
- `clientRequestId`: `fan-out-<slug>-<project>`, so a retry returns the same thread;
- `title`: the change and the project;
- `message`: pointers only:

```
Notes: /tmp/fan-out-<slug>/notes.md (read it first; its shared names are exact)
Your part: § <project>
Run the `implement` skill.
```

Invoking this skill is the user's request for these threads. Each child opens and babysits its
own PR ([THREADS.md](../implement/THREADS.md), "A launched thread reports to its own inbox").
Record each child's `threadId` and `link` in the notes file.

## 4. Track and report

`list_thread_pull_requests` with each child's `threadId` gives its PR and state; it is the only
source for a child's PR. Report one row per **in** project:

| Project | Thread | PR | State |
| ------- | ------ | -- | ----- |

with the thread's `link` verbatim. Name every child that has not opened its PR yet: nothing wakes
the coordinator for it, so the user asks again later and this step runs again. When the user
hands the coordinator a merge that is theirs, follow THREADS.md's launcher rule for each PR.

## 5. Order the merges

When the change comes from an agent-workflow PR, link every project PR from its body, then:

- a project PR that only adds what a new required contract row asks for merges before the shared
  PR, so the row is met the moment it lands;
- a project PR that renames something the shared files name merges together with the shared PR,
  back to back, so neither side reads a name the other has dropped.

Say which order applies to each PR in the step 4 report.
