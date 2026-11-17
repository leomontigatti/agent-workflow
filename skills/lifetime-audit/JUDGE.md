# Lifetime judge

The brief for one judge of the `lifetime-audit` skill. Your task names a checkout, its commit and
one slice: a list of files, each with the score and signals a scan gave it. Judge the whole slice,
following each file's async starts into the code it calls; the signals say where to look first.

The checkout is read-only. Read, search, read history (`git log`, `git show`, `git blame`) and
read the issue tracker; change no file, install nothing, run nothing that writes. The project's
`AGENTS.md` routes to its domain terms and coding standards, and `docs/agents/issue-tracker.md`
§ Conventions to the tracker.

A low score is no proof of safety: files the scan ranked last have held real bugs. A wrong
suspicion costs little, since a separate prover tests each one; a bug you pass over is the
expensive mistake. Every claim cites a `file:line` or a commit.

## The lifetime question

For every **async start** in the slice (a request, an await, a callback, a timer, a queued job, an
acquired resource, a read that a later write depends on), answer three things:

1. **Premise**: what did it assume when it started? The roster it asked about, the state it read,
   the screen it belongs to.
2. **Landing**: when it lands, can that premise have changed, and does the code check? Trace the
   interleaving step by step: the input still editable while the request is in flight, the reset
   that leaves the request live, the second request that overtakes the first, the write by id
   after a read of the state, the job that runs after its row moved on. Check what the framework
   already guarantees (a router that cancels stale loads, a database lock) before calling it
   stale.
3. **Release**: what it acquired or claimed is given back on every exit, a throw included. A
   resource is released; a claim (a cleared due time, a pending flag, a lock, a row marked in
   progress) is restored or settled. Walk each call after the claim and ask what happens when it
   throws: the error branch, the loop it runs in, the alarm or handler that called it, the
   unmount.

Then, for each area of the slice (a module, a flow):

4. **Shape**: the states and transitions as implemented. Where each piece of state lives (component
   state, a ref, a column, a nullable timestamp, a derived value) and which code moves it. A move
   written in two places with their own guards is a duplicate; one helper called from two
   triggers is not.
5. **History**: up to the 10 latest fix commits on the area (`git log --format='%h %s' -- <files>`,
   then `git show`). Name each that was a lifetime or shape bug.
6. **Backstop**, for each bug you found: what a later layer does with it (the server re-validating
   a save, a constraint refusing a write), and so whether the hit is **silent** (data lost or
   wrong, and nobody notices) or **loud** (an error someone sees and retries, nothing lost).
7. **Likelihood**, for each bug you found: the actors on each side and the window between them,
   from `docs/agents/review.md` § Hotspots or, where it names none, from the entry points that
   reach each side; for an edge case, what produces its input or stored state. Name the
   frequencies as a guess when no measurement backs them.

## Verdict

Two answers, each exactly one value:

- **Bug**: `traced` (a concrete interleaving or exit that goes wrong, traced through the code),
  `suspected` (a plausible one you could not trace to the end; say where the trace stops) or
  `none`. For each bug: the claim in one line, the sequence that triggers it, what happens instead
  and the test that would go red on it (its entry point, its steps, its assertion).
- **Shape**: `explicit` (states and transitions named and owned in one place; a discriminated
  union with pure transitions counts), `worth-fixing` (a duplicated transition, or flags that
  combine into a state nobody designed: sketch the explicit version in a few lines) or `leave`.

A fix sketch defaults to the smallest change: a request key, a guard in the `where`, a `finally`,
a discriminated union with pure transitions. Name a state-machine library only when the area needs
nested or parallel states, timers that survive a reload, spawned processes or durable actors.

Then **confidence** (low, medium, high).

**Tracked**: before reporting a bug, search the tracker's open and closed issues for it. A bug
already tracked is reported with its number and the word `tracked`; the audit cites it instead of
proving it again.

## Report

Your final message, under 900 words: Bug and Shape with confidence; each bug as above, tracked
ones with their number; the six answers, short. Write no files.
