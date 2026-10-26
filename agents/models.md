# Roles and models

The one place that says which model each agent role runs on. A skill names a role; this table
names its model. The harness wrappers in `claude/` and `codex/` repeat a model only where their
harness reads it from nowhere else, and a change here changes them in the same commit.

## The rule

**A different family from the author, whenever both are reachable.** The author is the family of
the session that wrote the code or the text being judged: Claude when Claude Code orchestrates,
Codex (Sol) when Codex does. A role that judges, reviews or hunts runs on the other family, so it
does not share the author's blind spots. A role that produces alternatives runs on both, so the
panel is diverse. Only a role that does the author's own work (implementing, mapping the codebase
for it) stays on the author's family. When only one family is reachable, the role runs on its
fallback, and the report says the role ran same-family.

Effort starts at the row's level. Raise it one step for the hardest work (a migration, a
concurrency bug, a design nobody has settled); lower it for routine reading. A change of effort
keeps the family, so a diverse panel stays diverse.

A task can run on a different model than its row names when that model fits it better (a
judgment too hard for the light model, say). The family rule still holds, and the report names
the model and why, as it does for a fallback.

| Role                  | What it does                                              | Model                                                    | Effort  | Fallback                                     |
| --------------------- | --------------------------------------------------------- | -------------------------------------------------------- | ------- | -------------------------------------------- |
| Standards, Spec       | `code-review`'s two axes                                  | the other family: Sol, or Opus when Codex wrote it       | medium  | `reviewer-opus` (Claude) / `reviewer` (Codex) |
| Correctness           | the bug hunt, `code-review`'s correctness brief          | the other family: Sol, or Opus when Codex wrote it       | medium  | same-family, recorded                        |
| Readback              | restates a diff                                           | Codex `gpt-6-luna`, or Claude Sonnet when Codex wrote it | low     | same-family, recorded                        |
| Design runners        | `codebase-design`'s design-it-twice, `prototype` variants | both families, alternating: Opus, Sol, Opus…             | high    | one family, at the same count                |
| Research              | primary sources outside the repo (`research` agent)       | Codex `gpt-6-luna`                                       | medium  | Claude `research` on Sonnet                  |
| Miners                | slices of transcripts or diffs (`retro`, `upstream-review`, `t3-update-review`) | Codex `gpt-6-luna`                 | low     | Claude Sonnet                                |
| Implementer           | one ticket (`implement-spec`)                             | the author's family: Opus (`claudeAgent`) in Claude Code, `gpt-6.1-sol` (`codex`) in Codex | medium in Codex | none                     |
| Codebase mapping      | a narrow read of 4+ files for the session                 | the harness's own explorer (Claude's `Explore`, Codex's default agent) | default | inline                       |

Model ids: Sol is `gpt-6.1-sol`, Luna is `gpt-6-luna` (Codex); Opus is `claude-opus-5-5`, Sonnet is
`claude-sonnet-5-5` (Claude).

Why each effort:

- **Standards, Spec**: breadth. Every hunk is matched against a list (the documented rules, the
  spec's lines); tracing one path in depth is the correctness axis's job.
- **Correctness**: depth on a traced path; raise it for a migration or concurrency diff.
- **Readback** and **Miners**: restating and sorting need little reasoning, and the light model
  spares the heavy one's quota.
- **Design runners**: each must find a radically different design, the costliest thinking here.
- **Research**: reading and citing sources, not reasoning across them.

The two-family trial a project's `docs/agents/review.md` may turn on (correctness on both
families in the full tier) is temporary: it gathers the numbers that will settle whether one
family is enough, and then this table changes.

## Reaching each model

- **Claude Code in a T3 thread**: the main session calls `delegate_task` once per Codex role,
  with `target: {providerInstanceId: "codex", model, options: {reasoningEffort}}` from the table.
  A Claude role is the Agent tool: `reviewer-opus` for a review, the general agent with the
  model set for the rest.
- **Codex**: a Claude role goes through T3's `delegate_task` with
  `target: {providerInstanceId: "claudeAgent", model}`; a Codex role is a native agent
  (`reviewer`, `reviewer-luna`, `research`).
- **The Implementer**, from either harness, is a `delegate_task` child with
  `isolation: "worktree"`, for the checkout T3 prepares; it has no harness wrapper.
- **Outside T3** (no `delegate_task`): the fallback column.

When a call refuses a model id, `orchestrator_capabilities` lists the live ones; fix the table
and the wrappers together.

## The briefs

Each role's instructions are one file here, read by every way the role runs:
[`reviewer.md`](reviewer.md), [`research.md`](research.md), [`implementer.md`](implementer.md).
A `delegate_task` child is told to read the brief at its installed path,
`~/.agents/workflow/agents/<brief>.md`, before anything else.
