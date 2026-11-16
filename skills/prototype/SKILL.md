---
name: prototype
description: Build a throwaway prototype to answer a design question. Use when the user wants to sanity-check whether a state model or logic feels right, or explore what a UI should look like.
---

# Prototype

A prototype is **throwaway code that answers a question**. The question decides the shape.

## Pick a branch

Identify which question is being answered, using the user's prompt, the surrounding code, or by asking if the user is around:

- **"Does this logic / state model feel right?"** → [LOGIC.md](LOGIC.md). Build a single shareable HTML file (free-play buttons plus tabbed guided walkthroughs) that pushes the state machine through cases that are hard to reason about on paper, and that a non-developer can drive.
- **"What should this look like?"** → [UI.md](UI.md). Generate structurally different UI variations (one, for a change with no real choice) on the real routes, switchable via a URL search param and a floating bottom bar; the user picks the winner in a live preview.

The two branches produce very different artifacts, so getting this wrong wastes the whole prototype. If the question is genuinely ambiguous and the user isn't reachable, default to whichever branch better matches the surrounding code (a backend module → logic; a page or component → UI) and state the assumption at the top of the prototype.

## Rules that apply to both

1. **Throwaway from day one, and clearly marked as such.** Locate the prototype code close to where it will actually be used (next to the module or page it's prototyping for) so context is obvious, but name it so a casual reader can see it's a prototype, not production.
2. **Trivial to run.** A UI prototype starts from one command in the project's own task runner, which `docs/agents/validation.md` lists. A logic demo is a single HTML file the user double-clicks. Either way, no thinking required to start it.
3. **No persistence by default.** State lives in memory. Persistence is the thing the prototype is _checking_, not something it should depend on. If the question explicitly involves a database, hit a scratch DB or a local file with a clear "PROTOTYPE, wipe me" name.
4. **Skip the polish, pass the gates.** No tests, no error handling beyond what makes the prototype _runnable_, no abstractions. The point is to learn something fast. The project's lint and type check still apply, since the winner's markup is what the implementation copies; the project's other gates treat a `prototype/` branch as `docs/agents/verification.md` § Prototype says, when it has one.
5. **Surface the state.** After every action (logic) or on every variant switch (UI), print or render the full relevant state so the user can see what changed.
6. **Capture it when done.** Commit the prototype to a `prototype/<issue>` branch (`prototype/<PRD>` for a spec's pass, `prototype/<short-name>` when no issue exists yet), push it, and keep it out of main: it is the **primary source** the implementation follows. Then comment on the issue: the answer and the question it settled (for a UI prototype, the winner and why it won), the branch, what the prototype left open for the implementer, and, for a UI winner, every project style rule it breaks (the user's pick overrules them, and the implementation's PR changes those rules). Show the comment to the user before posting it. With no issue yet, the same text goes in your reply, and the issue or spec a later step files carries it. Main keeps only what the implementation builds.
