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
SHA appears within five minutes: run § Heavy's commands here with the rest, and the final report
says they ran here and why. The remote never blocks the run.

## 3. Wait for it

In Claude Code, run `gh run watch <run-id> --exit-status` with Bash `run_in_background: true`,
then run the rest of § Before committing here; when those are clean, call `t3_background_wait`
with the watch's task ID (outside T3, the background command's completion wakes the session).
A harness with no background command (Codex) runs the rest first, then the same watch in the
foreground.

## 4. Read the result

Read the named job's conclusion, not the run's: `gh run view <run-id> --json jobs`.

- **success**: green on that SHA.
- **failure** or **timed_out**: red here too. Read its log uncut with
  `gh run view --job <job-id> --log-failed`, fix it here, commit, push, and start again from § 2
  on the new SHA.
- **skipped**: when a job it `needs` failed, that job's failure is red as above. When the
  workflow's own skip rule matches the diff, the commands did not run: the final report says so,
  with the rule. Otherwise run § Heavy here.
- any other conclusion (**cancelled**, **startup_failure**, **action_required**), or the run never
  finishes: a remote that did not answer. Run § Heavy here, and the final report quotes why.

## 5. Later commits

Each later commit (a review fix, a merge from the base) needs a green job on the head the run ends
on: the PR's CI run on that head counts. A commit that touches only files the workflow's own skip
rule ignores (docs, in a workflow that skips them) needs none, since CI skips it too; the report
names the SHA that last ran green.

Done when every § Heavy command is green on the commit the run ends on, in CI or here, or the
report says why it was not run.

The final report shows, for each § Heavy command: where it ran (the workflow, job and run URL, or
here and why), the SHA and the result.
