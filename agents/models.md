# Roles and models

The one place that says which model each agent role runs on. A skill names a role; this table
names its model, and nothing else names one.

## The rule

**A different family from the author, whenever both are reachable.** The author is the family of
the session that wrote the code or the text being judged: Claude when the thread runs on a Claude model, Codex when it runs on a GPT model. A role that judges, reviews or hunts runs on the other family, so it
does not share the author's blind spots. A role that produces alternatives runs on both, so the
panel is diverse. Only a role that does the author's own work (implementing, mapping the codebase
for it) stays on the author's family. When only one family is reachable, the role runs on its
fallback, and the report says the role ran same-family.

Effort starts at the row's level. Raise it one step for the hardest work (a migration, a
concurrency bug, a design nobody has settled); lower it for routine reading. A change of effort
keeps the family, so a diverse panel stays diverse.

When a role's result falls short, climb this **ladder** and stop at the first rung that fixes it:

1. Give the role a check it can run on its own work: a test, a build, a script.
2. Raise effort one step, up to high.
3. Move to the next model up in the same family, one effort step below what the smaller model
   ran. Past high, one more effort step costs about as much as that model.

With no rung left, stop and report the shortfall and the rungs tried.

A task can run on a different model than its row names when that model fits it better (a
judgment too hard for the light model, say). The family rule still holds, and the report names
the model and why, as it does for a fallback.

A provider can run another model than the one asked for. When the platform reports the model
that ran, the report names it, and its tier and family are the review's; otherwise the requested
model stands.

| Role                  | What it does                                              | Model                                                    | Effort  | Fallback                                     |
| --------------------- | --------------------------------------------------------- | -------------------------------------------------------- | ------- | -------------------------------------------- |
| Standards, Spec       | `code-review`'s two axes                                  | the other family: Sol, or Opus when Codex wrote it       | medium  | the author's family, recorded                |
| Correctness           | the bug hunt, `code-review`'s correctness brief          | full tier: both, Opus and Sol; else the other family: Sol, or Opus when Codex wrote it | medium  | one family, recorded                         |
| Lifetime judges       | one candidate area each (`lifetime-audit`)                | the other family: Sol, or Opus when Codex runs the audit | medium  | the author's family, recorded                |
| Lifetime provers      | one claim each, a failing test (`lifetime-audit`)         | the audit's own family: Opus or Sol                       | medium  | inline                                       |
| Readback              | restates a diff                                           | Terra, or Sonnet when Codex wrote it                     | low     | same-family, recorded                        |
| Design runners        | `codebase-design`'s design-it-twice, `prototype` variants | both families, alternating: Opus, Sol, Opus…             | high    | one family, at the same count                |
| Research              | primary sources outside the repo ([`research.md`](research.md)) | Terra                                              | low     | Sonnet                                       |
| Miners                | slices of transcripts or diffs (`retro`, `upstream-review`) | Terra                                  | low     | Sonnet                                       |
| Implementer           | one ticket (`implement-spec`)                             | the author's family: Opus or Sol                          | medium  | none                     |
| Codebase mapping      | a narrow read of 4+ files for the session                 | a subagent on the thread's own model                      | low     | inline                       |

Sol, Terra and Luna are the Codex family; Opus and Sonnet the Claude family. Their ids are in
the `model-ids` block under [Reaching each model](#reaching-each-model).

Why each effort:

- **Standards, Spec**: breadth. Every hunk is matched against a list (the documented rules, the
  spec's lines); tracing one path in depth is the correctness axis's job.
- **Correctness**: depth on a traced path; raise it for a migration or concurrency diff. High
  effort elsewhere buys little: it turned 1 of 11 bugs a model missed at medium into a catch.
- **Lifetime judges**: depth on one slice's async starts, traced through its history. On rubens
  (2026-11-17), Sol at medium traced 15 bugs in 10 areas, 5 of them already tracked; provers
  turned all 10 new ones red. Opus at low, reading the same files as a general bug hunt, flagged
  none of the 15.
- **Lifetime provers**: a test written from the claim alone, by the family that did not make the
  claim, so the judge's reasoning reaches it only through the code.
- **Readback**: restating a diff needs little reasoning, and the light model spares the heavy
  one's quota. On #119 and #92, read twice each (2026-11-13), Terra named the change the
  commit title left out in 4 of 4 runs and Luna in none, for 1.4 times the tokens.
- **Miners**: sorting needs little reasoning, but a slice is tens of kilobytes to read to the end.
  On the same two slices (retro, 2026-11-09), Luna dropped a session and missed the main
  friction of another, Haiku cited wrong transcript lines, and Terra matched Sonnet's blocks.
- **Design runners**: each must find a radically different design, the costliest thinking here.
- **Research**: reading and citing sources, not reasoning across them. A source is long input
  like a miner's slice, where Luna dropped content; research itself is unmeasured on either.

Why correctness runs on both families in the full tier: on 15 known bugs
([reviewer-recall](../evals/reviewer-recall/README.md), 2026-10-27), Opus caught 63% of its
reviews' bugs and Sol 40% (on `gpt-6.1-sol`; 6.2 is unmeasured), each finding bugs the other missed, and the two together caught 14
of 15. A diff outside the full tier keeps one reviewer, to spare the quota.

## Reaching each model

Every role starts fresh, from its brief alone, never as a fork of this session: a fork inherits the
author's reasoning, the blind spot a judging role exists to escape.

A session runs as a Capy thread, and the author's family is the family of the thread's model. Each
role is a **subagent** of that thread, started with the row's model and effort in its `model`
field: `{model_id, reasoning_mode}`, where `reasoning_mode` is the table's effort and `model_id` is
the model's line below: the provider, a slash, then the model. This block is the one place a
role's id is written; `review.py tier` reads it, one `<Name>: <id>` per line.

```model-ids
Sol: openai/gpt-6.2-sol
Terra: openai/gpt-6.1-terra
Luna: openai/gpt-6-luna
Opus: anthropic/claude-opus-5-5
Sonnet: anthropic/claude-sonnet-5-5
```

- **A subagent shares the thread's machine and checkout, or gets a machine of its own** with a
  clean checkout. A judging role shares: it reads there, uncommitted work included, and writes
  nothing. A role that writes gets its own machine, so two writers never share a checkout.
- **Each family runs on the user's connected subscription** for it. A start that is refused (a
  model id, an effort, an exhausted subscription) is reported with its exact error, then the role
  runs on the fallback column and the report says so. When an id is refused, list the platform's
  models and fix the table.
- **Size a fan-out before starting it.** Count the children and their rounds first. More than 8
  on one family run in batches of 8, each batch read before the next starts, so a subscription
  limit stops a batch and not the whole run.
- **The Implementer** is a subagent on its own machine; it pushes its branch, since the
  orchestrator's machine cannot see its files.
- **Work in another project** is a thread started in that project, on the row's model. It boots
  on that project's Setup and its result comes back as a message that wakes this thread. A
  thread started in this same project reports only when its prompt tells it to message this
  one.
- **Nothing shows how much of a subscription is left.** A limit shows as a failed model call:
  stop the fan-out there, report what ran and what did not, and leave the rest for the user's
  word.

A role run above its row (the ladder, the hardest work) is the same start with the higher model or
effort in `model`.

## The briefs

Each role's instructions are one file here, read by every way the role runs:
[`reviewer.md`](reviewer.md), [`research.md`](research.md), [`implementer.md`](implementer.md).
A subagent's task opens by telling it to read the brief at its installed path,
`~/.agents/workflow/agents/<brief>.md`, before anything else.
