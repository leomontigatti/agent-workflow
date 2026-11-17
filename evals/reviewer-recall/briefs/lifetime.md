# Correctness brief with the lifetime lens

A variant of the quoted brief in `skills/code-review/CORRECTNESS.md`, for
`run.py review --brief briefs/lifetime.md`. It adds the first three items of the lifetime-audit
judge's lifetime question (premise, landing, release) and folds in the stale-state item they
cover. Only the `>` lines reach the reviewer. When `CORRECTNESS.md`'s brief changes, change this
copy the same way, or the comparison measures two changes at once.

> Assume this diff has a bug its author's tests miss, and hunt for it. The stated intent is
> correct; challenge the execution. Read the callers and callees of every changed function,
> beyond the diff. Look where this codebase gets hurt: <the project's hotspots>. Look
> everywhere for: an action that runs twice, or stops halfway; a migration the previous
> release runs against during the deploy; empty, zero, null and boundary values; an error
> caught and dropped; a guard that hides a broken invariant where the invariant should be
> fixed; a rule the client and the server each enforce, in two copies that disagree; a second
> write path (another handler, route or job reaching the same record) missing the access or
> validation check the first one has; an HTTP header, cookie or cache directive that leaks,
> caches or blocks what it should not; a script that deletes or overwrites (a sync with delete,
> a reset, a restore) pointed at the wrong target or run with an empty variable; an existing
> test this diff deletes, skips or gives a new expected value, where the stated intent does not
> change that behaviour: name the behaviour it no longer pins.
>
> Then trace every **async start** in the diff (a request, an await, a callback, a timer, a
> queued job, an acquired resource, a read a later write depends on) through its lifetime:
> what it assumed when it started (the input, the record's state, the screen it belongs to);
> whether that can have changed by the time it lands (the input still editable, a reset,
> submit, reload or navigation that leaves it live, a second request that overtakes it, a write
> by id after the read) and whether the code checks; and whether what it acquired or claimed
> (a stream, a lock, a pending flag, a row marked in progress) is given back on every exit, a
> throw included.
>
> For each finding give its severity (`critical`: a wrong result, lost or corrupt data, a
> security hole; `warning`: holds today and breaks under a condition you can name, and how
> likely that condition is), the hunk (file and line), and the **path** that triggers it: the
> input or sequence of calls, traced through the code, that makes it go wrong. A traced race,
> at any severity, also gets its likelihood (who the concurrent actors are, how wide the window
> is, how often each side runs), what a hit costs (silent or loud), and what its fix would add. A suspicion you could not trace to a path goes
> under "Untraced", one line each. Style, naming and structure belong to another reviewer.
>
> End with one line: `Would merge: yes | after fixes | no`, and the finding that decides it.
> "No findings" is a valid review. Under 400 words.
