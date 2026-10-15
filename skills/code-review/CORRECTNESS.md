# Correctness

The bug-hunting axis of step 5 of the `implement` skill. It runs on every diff that changes
behaviour: beside the readback, or beside Standards and Spec in the full review. Standards asks
whether the code follows the repo's conventions and Spec whether it does what the issue asked;
this one asks whether it is **wrong**.

1. Use the fixed point, diff command and commit list pinned for `code-review`, or for the
   readback.
2. Spawn **one** correctness reviewer on the model family that did not write the code, as
   [Spawning a reviewer](SKILL.md#spawning-a-reviewer) says, in the same message as the other
   review spawns. When `docs/agents/review.md` asks for both families in the full tier, spawn one
   of each with the same prompt. The prompt carries the diff command, the commit list, one
   paragraph stating what the change is meant to do, the brief below, and
   `docs/agents/review.md` § Hotspots pasted in where the brief says.

   > Assume this diff has a bug its author's tests miss, and hunt for it. The stated intent is
   > correct; challenge the execution. Read the callers and callees of every changed function,
   > beyond the diff. Look where this codebase gets hurt: <the project's hotspots>. Look
   > everywhere for: an action that runs twice, or stops halfway; a migration the previous
   > release runs against during the deploy; empty, zero, null and boundary values; an error
   > caught and dropped; a guard that hides a broken invariant where the invariant should be
   > fixed; a rule the client and the server each enforce, in two copies that disagree; a second
   > write path (another handler, route or job reaching the same record) missing the access or
   > validation check the first one has; state that goes stale after a submit, a reload or a
   > navigation, or an effect or dialog that outlives what it belongs to; an HTTP header, cookie
   > or cache directive that leaks, caches or blocks what it should not; a script that deletes or
   > overwrites (a sync with delete, a reset, a restore) pointed at the wrong target or run with
   > an empty variable.
   >
   > For each finding give its severity (`critical`: a wrong result, lost or corrupt data, a
   > security hole; `warning`: holds today and breaks under a condition you can name), the hunk
   > (file and line), and the **path** that triggers it: the input or sequence of calls, traced
   > through the code, that makes it go wrong. A suspicion you could not trace to a path goes
   > under "Untraced", one line each. Style, naming and structure belong to another reviewer.
   >
   > End with one line: `Would merge: yes | after fixes | no`, and the finding that decides it.
   > "No findings" is a valid review. Under 400 words.

3. Report it under `## Correctness`, after `## Standards` and `## Spec` or after `## Readback`,
   verbatim or lightly cleaned, and add its count and worst finding to the closing summary line.
   With two reviewers, report each under its model's name, and mark each finding the other one
   also raised.
