---
name: fan-out
description: "Fan one change out across several projects: pick the projects, fix the shared wording, launch one thread per project, track their PRs."
disable-model-invocation: true
---

# Fan out a change

The argument is a change that has to land in several projects: most often a breaking
`contract.md` change from an agent-workflow PR, whose body names the projects and what each must
add or rename. This thread is the **coordinator**: it writes no project's code. Each project gets
its own thread, on its own machine, running its own contract through `implement`, and opens its
own PR. The coordinator owns the list, the shared wording and the report.

## 1. Scope

Discover the projects; keep no index of them. List the platform's projects, then:

- keep one entry per repository; two projects with similar names and different repositories are
  two repos;
- leave out the coordinator's own project: its change is the shared PR, not a child.

For each project left, read the top of `AGENTS.md` on its default branch
(`gh api repos/<owner>/<repo>/contents/AGENTS.md`), plus whatever the change touches there (a contract file,
a skill it renames). Mark it **in** or **out**, with a one-line reason. Show the user the list and
wait for their agreement.

Done when every project is in or out with a reason and the user has agreed to the list.

## 2. Fix the shared parts

Write the **notes** as one comment on the PR or issue the change comes from, opening
`## Fan-out notes` and edited in place from then on, since each child's machine sees only GitHub:

- the change, and the PR or issue it comes from;
- one section per **in** project: what that project must do, and its merge order (step 5);
- every name, heading, wording and file path that must be identical in every project, spelled
  out exactly once.

When a part changes something you cannot read from here (a project's Setup, a secret, a
dashboard), the notes are a guess. Start one project alone in step 3, whatever its size, with
one more line in its message: "Message the thread that started you with what you found there
before you change it." Add what it reports to the notes, then start the rest.

The notes are the single source of truth for what is shared, so the children stay in step. A
question a child raises about shared wording is answered in the notes, then pointed at.

## 3. Launch one thread per project

Each child is a thread started in its project, on the thread's own model, titled with the
change and the project. Its message is pointers only:

```
Notes: the `## Fan-out notes` comment on <URL> (read it first; its shared names are exact)
Your part: § <project>
Run the `implement` skill, then commit, push, open your PR and babysit it.
When your PR is open, and again when it is ready, message the thread that started you with its URL.
<only when your part merges with the shared PR:> Leave the merge to the user.
```

**Count the machines first.** Each child is a machine, and so is every Setup build it runs and
every subagent it starts on a machine of its own. Start each child at the size
[THREADS.md](../implement/THREADS.md) gives its part. Parts that take the project's size start
one at a time, each after the last has reported its validation finished (its PR ready, its
Setup's test build passed) or that it is blocked, so the organization's memory cap stops no
build halfway through the run. A start refused for memory is retried once, a few minutes later,
when the last machine has slept; refused again, other work holds the cap, and the report in
step 4 names the parts not started. The smaller parts start together.

Invoking this skill and agreeing to the step 1 list is the user's whole go-ahead for these
threads: start every **in** project without asking again. Each child opens and babysits its
own PR and stops at READY: the merges are the user's
([THREADS.md](../implement/THREADS.md)). Record each child's thread in the notes.

## 4. Track and report

Each child's message gives its PR; read that PR's state from GitHub (`gh pr view <url> --json
state,mergeStateStatus,statusCheckRollup`), never from the child's word. Report one row per
**in** project:

| Project | Thread | PR | State |
| ------- | ------ | -- | ----- |

Name every child that has not opened its PR yet. When the user asks for the merges in this
thread, merge each PR that reads READY, in step 5's order.

## 5. Order the merges

When the change comes from an agent-workflow PR, link every project PR from its body, then:

- a project PR that only adds what a new required contract row asks for merges before the shared
  PR, so the row is met the moment it lands;
- a project PR that renames something the shared files name merges together with the shared PR,
  back to back, so neither side reads a name the other has dropped. It waits at READY until
  the user merges both, or asks the coordinator to.

Say which order applies to each PR in the step 4 report.
