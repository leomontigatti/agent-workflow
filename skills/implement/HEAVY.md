# Heavy commands on a linked machine

A project's `docs/agents/validation.md` § Heavy names the commands of § Before committing that
are worth sending to a linked machine (a browser suite, the full CI job), the install a stale
checkout needs before them, and optionally the link to use. Step 3 of `implement` runs those
there and the rest of § Before committing here. The rules for the machine itself (how to wake it,
how long to wait, how files cross) live in the user's instructions and the host doc they point
to; read them first.

## 1. Pick the machine

`t3_environment_links` lists the linked machines and whether each answers. Take the link § Heavy
names, else the one the user's instructions send heavy validation to. When it does not answer,
wake it and wait for its link the way those instructions say.

**Fall back here** when there is no T3 (no `t3_environment_links`), no link is listed, or the
link still does not answer at the end of that wait: run § Heavy's commands here with the rest,
and the final report says they ran here and why. The remote never blocks the run.

## 2. Push the exact commit

The machine has only what is pushed, so this commit comes before step 6: commit the work so far,
with step 6's message rules, push the branch, and note the commit's full SHA. Later fixes, and
step 6, add commits on top. A run where step 6 will not commit runs § Heavy here.

## 3. Delegate one runner

Call `delegate_task` with `target.environmentId` set to the link's, the **Heavy runner** of
`agents/models.md` for the model, `role: "test"` and `mode: "async"`, and a task that carries:

- the repo, the branch, the full SHA, § Heavy's install and its commands, in order;
- the shared checkout's rules: the child works in that machine's checkout of the project, which
  other tasks use too and is usually stale. It runs one task there at a time, starts from a
  clean tree (when `git status --porcelain` prints anything, it stops and reports the output
  rather than discarding it), notes the branch or commit it found, fetches, checks out the SHA
  detached, runs the install, then each command in the foreground, and checks out what it noted
  when done, the tree clean again;
- that it fixes nothing and edits no tracked file: it reports;
- the report: per command, the command, the SHA it ran on, the exit code, and on a non-zero exit
  the failing output verbatim (the failure's own lines, uncut), then that the checkout was
  restored.

Run the rest of § Before committing here meanwhile. When those are clean and the runner has not
reported, end the turn: its completion wakes the thread.

## 4. Read the result

A red result there is red here: fix it here, commit, push, and send § Heavy again on the new SHA.
Any other outcome without an exit code for every command is a remote that did not answer: the
call refused, the link dropped, the runner cancelled or stopped on a dirty checkout, the install
or the checkout failed. Run § Heavy here, and the final report quotes why. When the runner did
not report the checkout restored, the final report also names the machine and the checkout left
to restore.

Each later pass through step 3 (after review fixes) sends § Heavy again on its new SHA.

Done when every § Heavy command exits 0 on the commit the run ends on, there or here.

The final report shows, for each § Heavy command: where it ran (the link's name, or here and
why), the SHA and the exit code.
