# Roles and models

The one place that says which model each agent role runs on. A skill names a role; this table
names its model. The harness wrappers in `claude/` and `codex/` repeat a model only where their
harness reads it from nowhere else, and a change here changes them in the same commit.

| Role                     | Provider    | Model             | Effort  | Fallback                                                       |
| ------------------------ | ----------- | ----------------- | ------- | -------------------------------------------------------------- |
| Standards, Spec          | Codex       | `gpt-6.1-sol`     | medium  | Claude Code outside T3: `reviewer-opus`                        |
| Readback                 | Codex       | `gpt-6-luna`      | low     | Claude Code outside T3: `reviewer-opus`                        |
| Correctness, Claude code | Codex       | `gpt-6.1-sol`     | medium  | Claude Code outside T3: `reviewer-opus`, recorded as same-family |
| Correctness, Codex code  | Claude      | `claude-opus-5-5` | default | outside T3: `reviewer`, recorded as same-family                |
| Research                 | Codex       | `gpt-6-luna`      | medium  | Claude Code outside T3: `research` on Sonnet                   |
| Implementer              | the harness | Opus in Claude Code, `gpt-6.1-sol` in Codex | medium in Codex | none                       |

Why each effort:

- **Standards, Spec**: breadth. Every hunk is matched against a list (the documented rules, the
  spec's lines); tracing one path in depth is the correctness axis's job.
- **Readback**: restating a diff and flagging what jars needs little reasoning, and Luna spares
  the Sol quota.
- **Correctness**: the family that did not write the code hunts the bugs, so the hunt does not
  share the author's blind spots. Opus keeps the Claude agent's own effort.
- **Research**: reading and citing sources, not reasoning across them.

## Reaching each model

- **Claude Code in a T3 thread**: the main session calls `delegate_task` once per Codex role,
  with `target: {providerInstanceId: "codex", model, options: {reasoningEffort}}` from the table.
  An Opus role is the `reviewer-opus` agent, spawned with the Agent tool in the same message.
- **Codex**: the native agents, `reviewer` for Standards, Spec and Sol correctness,
  `reviewer-luna` for the readback, `research` for research. An Opus role goes through T3's
  `delegate_task` with `target: {providerInstanceId: "claudeAgent", model: "claude-opus-5-5"}`.
- **Outside T3** (no `delegate_task`): the fallback column.

When a call refuses a model id, `orchestrator_capabilities` lists the live ones; fix the table
and the wrappers together.

## The briefs

Each role's instructions are one file here, read by every way the role runs:
[`reviewer.md`](reviewer.md), [`research.md`](research.md), [`implementer.md`](implementer.md).
A `delegate_task` child is told to read the brief at its installed path,
`~/.local/share/agent-workflow/agents/<brief>.md`, before anything else.
