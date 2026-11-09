# Heavy commands in CI

A project's `docs/agents/validation.md` § Heavy names the commands of § Before committing that
its CI runs instead of the session (a browser suite, a long integration job), and the workflow
and job that run them. Step 3 of `implement` reads their result from that job and runs the rest
of § Before committing here. A CI job gives a clean machine and the command's real exit code.

## 1. Push the exact commit

CI sees only what is pushed, so this commit comes before step 6: commit the work so far, with
step 6's message rules, push the branch, and note the commit's full SHA. Later fixes, and step 6,
add commits on top. A run where step 6 will not commit runs § Heavy here.

## 2. Start the run

Once the PR is open, its own CI run on that head counts: skip the dispatch and find it as below.
Before then, dispatch the workflow § Heavy names on the pushed branch:

```sh
gh workflow run <workflow> --ref <branch>
gh run list --workflow <workflow> --commit <sha> --json databaseId,headSha,status
```

A dispatch runs the branch head, so the run that counts is the one whose `headSha` is the pushed
SHA. A new run can take a minute to appear: list again before falling back.

**Fall back here** when the repo has no such workflow, the dispatch is refused, or no run for the
SHA appears within five minutes. Read the workflow's own skip rule against the diff it judges (for
a rule on the branch's diff, `git diff --name-only <base>...<sha>`). When it matches, CI would have
skipped the commands too: they do not run here either, and the final report says so, with the rule
and why the remote did not answer. Otherwise run § Heavy's commands here with the rest, and the
final report says they ran here and why. The remote never blocks the run.

## 3. Wait for it

The watch is `timeout 1800 gh run watch <run-id> --exit-status`: 30 minutes, after which the run
counts as one that never finishes (§ 4). In Claude Code, start it with Bash
`run_in_background: true`, then run the rest of § Before committing here; when those are clean,
call `t3_background_wait` with the watch's task ID (outside T3, the background command's
completion wakes the session). A harness with no background command (Codex) runs the rest first,
then the watch in the foreground.

## 4. Read the result

Read the named job, not the run: `gh run view <run-id> --json jobs` gives the job's `conclusion`
and its `steps[]`, each with a `name` and a `conclusion`. A workflow can skip a command at step
level while its job still succeeds, so find the step that runs each § Heavy command, by its name or
its `run:` line in the workflow, and read it too.

- **success**, with each command's step `success`: green on that SHA.
- **failure** or **timed_out**: red here too. Read its log uncut with
  `gh run view --job <job-id> --log-failed`, fix it here, commit, push, and start again from § 2
  on the new SHA.
- **skipped**, the job or a command's step: when a job it `needs` failed, that job's failure is
  red as above. When the workflow's own skip rule (a job's or a step's `if:`) matches the diff,
  the commands did not run: the final report says so, with the rule. Otherwise fall back (§ 2).
- any other conclusion (**cancelled**, **startup_failure**, **action_required**), the named job
  missing from the run, or the run never finishes: a remote that did not answer. Fall back
  (§ 2), and the final report quotes why.

## 5. Later commits

Each later commit (a review fix, a merge from the base) needs the § Heavy commands green on the
head the run ends on: §§ 2 to 4 again on that head, where once the PR is open its own CI run is
the run, and § 2's fallback still holds.

- **A merge from the base** always goes through them, whatever files it brings in. They are the
  base's, and a skip rule that reads the branch's diff against the base sees only the branch's own
  changes: a docs-only branch still skips by its rule, and a code branch runs on the merged code.
- **A commit of your own** that changes only files the skip rule ignores (docs, in a workflow that
  skips them) cannot change the commands' result, so the green on the head before it stands; the
  report names that SHA.

Done when every § Heavy command is green on the commit the run ends on, in CI or here, or the
report says why it was not run.

The final report shows, for each § Heavy command: where it ran (the workflow, job and run URL, or
here and why), the SHA and the result.
