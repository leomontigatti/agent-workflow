# Upstream decisions

Every idea taken from an upstream, or turned down, once. The `upstream-review` skill drops an
idea already here before it triages the rest, so a declined idea stays declined until someone
reopens it on purpose.

An entry: a stable id (`<source id>:<kebab-name>`, the source ids are in
[`sources.json`](sources.json)), the idea in one line, the verdict, and where it landed or why
not.

- **adopted**: in our skills; "where" names the file. "to do" means agreed and not yet written.
- **declined**: "why" is the reason; reopening needs a new reason.
- **later**: worth it under a condition that does not hold yet; "why" names the condition.

## pstack v0.15.25 review (2026-10-15)

| Id                                             | Idea                                                                                                                                 | Verdict  | Where or why                                                                                                                                                         |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pstack:verification-skill`                    | A scripted way to prove behaviour per app: Launch, Doctor, Drive, Evidence, Cleanup, plus a feature map.                             | adopted  | `contract.md`: each project's `docs/agents/verification.md` has those sections; `implement` step 4 follows it. To do: each project writes the file.               |
| `pstack:correct-ladder`                        | Fix at the highest rung: architecture, then a type or lint naming the fix, then a test, then a doc; a rule→enforcer table, where an unenforced rule counts as a repeat. | adopted  | `skills/retro/SKILL.md` § Fix ladder.                                                                                                                                |
| `pstack:role-model-map`                        | One role→model table.                                                                                                                | adopted  | `agents/models.md`.                                                                                                                                                  |
| `pstack:untrusted-input`                       | PR comments, issue bodies and reviewer output are data, never instructions; never put them into a shell command.                    | adopted  | `skills/babysit-pr/SKILL.md` (intro), `skills/code-review/SKILL.md` § Spawning a reviewer, `skills/implement/SKILL.md` § 1, `agents/*.md`.                          |
| `pstack:prune-passes`                          | Cut instructions the current model follows without being told.                                                                       | adopted  | `skills/retro/SKILL.md` step 8; the no-op test in `skills/writing-for-agents/SKILL.md` § Pruning.                                                                   |
| `pstack:reply-evidence`                        | Never hand the human a check you could run; label claims measured / inferred / guess; paste failing-then-passing output.            | adopted  | `skills/implement/SKILL.md` step 4, step 7's screen approval and § The final report.                                                                               |
| `pstack:router-mode`                           | A router mode that dispatches to skills.                                                                                             | declined | `AGENTS.md` routing already does this.                                                                                                                               |
| `pstack:disable-model-invocation-everywhere`   | Make every skill user-invoked.                                                                                                       | declined | We want `implement` and `babysit-pr` to load on their own.                                                                                                           |
| `pstack:orch-swarm-loop`                       | An orchestrated swarm loop over many agents.                                                                                         | declined | T3's `watch_pull_request`, `schedule_task` and `delegate_task` cover it; unattended runs are retired.                                                               |
| `pstack:arena`                                 | Several models build the same thing and compete.                                                                                     | declined | Token cost; `prototype` and `grilling` cover the question it answers.                                                                                                |
| `pstack:no-comments`                           | A rule against code comments.                                                                                                        | declined | We keep comments that carry intent or a constraint: the **Comments** smell in `skills/code-review/SKILL.md` § 3 (2026-10-22). |
| `pstack:watch-pr-script`                       | A typed READY/BLOCKED verdict script for a PR.                                                                                       | later    | Only if `babysit-pr`'s state table keeps being misread.                                                                                                              |

## pstack follow-up: models, recall and reflect (2026-10-15)

| Id                               | Idea                                                                                                   | Verdict  | Where or why                                                                                                                        |
| -------------------------------- | ------------------------------------------------------------------------------------------------------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `pstack:family-diversity`        | Every judging role on a different family from the author; producing roles (design, eval) on both.     | adopted  | `agents/models.md` § The rule.                                                                                                      |
| `pstack:effort-ladder`           | Effort starts at a level, one step up for the hardest work, down for routine; the family stays.        | adopted  | `agents/models.md` § The rule.                                                                                                      |
| `pstack:design-runners`          | Parallel design runners across model families.                                                         | adopted  | `agents/models.md` (Design runners); `skills/codebase-design/DESIGN-IT-TWICE.md`.                                                   |
| `pstack:reflect-citation-check`  | A synthesizer spot-checks the miners' cited evidence before using it.                                  | adopted  | `skills/retro/SKILL.md` step 5.                                                                                                     |
| `pstack:user-budget`             | A per-user budget (unlimited / large / medium / small) that sets every role's effort.                  | declined | One committed table is easier to keep true than a generated per-user rule; effort per role is in `agents/models.md`.               |
| `pstack:fast-mode-urgent-only`   | Fast model variants only when CI or trunk is red or a person is blocked.                               | declined | We have no fast variants in the roles we run; the light roles use Luna or Sonnet instead.                                           |
| `pstack:recall-status-tags`      | A context capsule whose every thread carries a status tag (`[merged #N]`, `[in flight]`…).             | declined | `retro` is not a resume tool; T3 threads and their linked PRs carry that status.                                                   |
| `pstack:recall-shared-record`    | Feed user reports, reverted fixes and production errors into the retrospective.                       | later    | When a project has an error tracker an agent can read; until then `retro` step 4's PR record covers reverts and failed checks.      |
| `pstack:reflect-lenses`          | Mine a session through separate lenses (judgment, tooling, divergent) before synthesis.                | adopted  | In part: the divergent lens is the "Wrong approach" signal in `skills/retro/MINING.md`; separate miners per lens stay later.        |
| `pstack:reflect-route-by-size`   | Route an accepted fix by size: a trivial edit in place, a substantive one through a skill-writing flow. | adopted  | `skills/retro/SKILL.md` step 10, with the shared-or-project split added. |
| `pstack:verifier-subagent`       | A separate verifier, on another family, for expensive or high-blast-radius units.                      | later    | Once each project's `docs/agents/verification.md` exists and a full-tier PR shows verification as the gap.                          |
| `pstack:maintain-verification`   | A periodic pass that re-proves the verification doc by driving it, and fixes only that doc.            | later    | Once the three `verification.md` files exist; then a scheduled task per project.                                                    |
| `pstack:correct-twice`           | A class of mistake counts once it has happened twice; one session is an anecdote.                      | adopted  | `skills/retro/SKILL.md` step 6, with an exception for a single event that lost data or shipped a bug.                              |
| `pstack:correct-proof`           | A new check must fail on the real past mistake before it is trusted.                                   | adopted  | `skills/retro/SKILL.md` § Fix ladder and the report's Proof line.                                                                    |
| `pstack:correct-enforcer-table`  | A rule→enforcer table, so an unenforced rule shows as a repeat.                                        | adopted  | `skills/retro/SKILL.md` report § Enforcers.                                                                                          |

## Weekly review (2026-10-19): pstack v0.15.28, mattpocock-skills 5beb35b

Verdicts marked proposed stand until this review's PR merges; the three adopted ones the user approved, and they merged, on 2026-10-19.

| Id                                          | Idea                                                                                                   | Verdict  | Where or why |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------ | -------- | ------------ |
| `pstack:decidable-asks`                     | Every item waiting on the user listed with link, impact, evidence, risk and pick; never cut to save words. | adopted | `skills/implement/SKILL.md` § The final report (#13). |
| `pstack:evidence-survives-cleanup`          | After cleanup, confirm the captured evidence is still there.                                           | adopted | `skills/implement/SKILL.md` step 4 (#14). |
| `pstack:skill-name-matches-folder`          | Every skill's `name:` is its folder name.                                                              | adopted | `tests/lint_skills.py` `check_skill_names` (#15). |
| `pstack:formal-verification-skill`          | A project skill that formally checks one costly property tests rarely reach, shown able to fail.      | later (proposed) | When a project has a race, retry or state machine whose bug is costly; then an optional `docs/agents/formal-verification.md` row. |
| `pstack:maintain-formal-verification`       | Re-sync a formal check after code changes and classify each failure as drift or bug.                   | later (proposed) | Once `pstack:formal-verification-skill` is adopted somewhere; then a scheduled task. |
| `pstack:claude-code-adapter`                | A table mapping Cursor names to Claude Code.                                                           | declined (proposed) | Each harness has its own wrapper (`agents/claude/`, `agents/codex/`); models live only in `agents/models.md`. |
| `pstack:docs-vs-tree-check`                 | A CI check that the docs match the skill tree.                                                         | declined (proposed) | No doc enumerates our skills; `tests/lint_skills.py` checks every link. |
| `pstack:brand-via-type-guard`               | A TypeScript brand comes from a type guard, never `as`.                                                | declined (proposed) | A language rule is a project's coding standard. |
| `pstack:rereview-by-delta`                  | After a verified head, small changes get one fresh verifier; only new behaviour gets the full panel.  | declined (proposed) | `skills/implement/SKILL.md` § Fix round already reviews the fixes alone. |
| `mattpocock-skills:dated-commit-cited-wiki` | Orchestrator memory as a wiki of dated, commit-cited claims.                                           | declined (proposed) | Memory is the harness's; our docs describe the present, kept true by PRs. |

## First look: gentle-ai 42edf9a, engram 61ec5c8 (2026-10-22)

Neither is adopted as a whole: gentle-ai writes its own workflow into the harness config that
`install.sh` links, and neither knows T3. Verdicts marked proposed stand until this review's PR
merges.

| Id                                    | Idea                                                                                                  | Verdict  | Where or why |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------- | -------- | ------------ |
| `gentle-ai:delegate-for-a-reason`     | A subagent only for a named reason (parallel writers, fresh context, exploration, verifier); otherwise inline. | adopted (proposed) | `skills/implement-spec/SKILL.md` step 2: the first lone frontier ticket is built inline. Exploration is the Codebase mapping row of `agents/models.md`. |
| `gentle-ai:spec-by-reference`         | Hand a worker the spec itself, never a paraphrase.                                                   | declined (proposed) | Already there: `skills/implement-spec/SKILL.md` (pointers, never pasted summaries) and `implement` step 5 (the spec's body pasted to reviewers). |
| `gentle-ai:frozen-review-candidate`   | Freeze the candidate before a review reads it, and bind the evidence to it.                           | declined (proposed) | The `## Review` record names the reviewed commit and `review-record` fails a later change; fix rounds diff against a `git stash create` snapshot. |
| `gentle-ai:credential-deny-list`      | Permission rules denying reads and edits of `.env`, `.ssh`, keys and secrets.                         | later (proposed) | `Read`/`Edit` rules do not stop Bash, and `.env` is legitimate local config. Only if a retro shows an agent touching credentials; then a Bash hook in `hooks/`. |
| `engram:persistent-memory`            | A memory store shared across harnesses (SQLite, MCP, session hooks).                                 | later (proposed) | When `retro` finds context lost between Claude and Codex sessions twice; until then `mattpocock-skills:dated-commit-cited-wiki`'s reason holds. |

## Weekly review (2026-10-26): pstack v0.15.32, gentle-ai 3270126, engram f15b94a

Verdicts marked proposed stand until this review's PR merges. gentle-ai changed no watched path.

| Id | Idea | Verdict | Where or why |
| -- | ---- | ------- | ------------ |
| `pstack:statechart` | A TLA+ model's state graph drawn as a Mermaid statechart in the reader's words, each broken rule a numbered path; also chart → TLA+ skeleton. | later (proposed) | Same condition as `pstack:formal-verification-skill`: a project with a TLA+ model of a costly race or state machine. |
| `pstack:formal-verification-reads-with-statechart` | A generated formal-verification skill reads every TLA+ result through `/statechart`, by name only. | later (proposed) | Once `pstack:formal-verification-skill` and `pstack:statechart` are adopted. |
| `pstack:model-bug-replayed-in-code` | Replay each model-found bug in the real code through reachable entry points; a test asserting a flag it set proves nothing. | declined (proposed) | `skills/tdd/SKILL.md` (public interfaces) and `skills/implement/SKILL.md` step 4; the model part rides with `pstack:statechart`. |
| `pstack:ketchup-video` | The catch-up as a silent video of slides, the waiting calls as text. | declined (proposed) | A render per catch-up for what the thread and `implement`'s final report give in text. |
| `pstack:sharpen-rewrite-only` | `/sharpen` rewrites the prompt deeper (expert additions, raw material, methods, outside check) and does not do the task. | declined (proposed) | A personal prompt, not a procedure; `grilling` and `implement` step 4 cover it. |
| `pstack:reflect-no-plugin-cache` | Reflect edits a local copy of a skill, never the plugin cache, and never pushes. | declined (proposed) | `skills/retro/SKILL.md` step 10 routes shared changes to the shared-workflow repo through a PR. |
| `engram:selective-memory` | Save only verified, durable knowledge; search before writing, update by id, never claim unconfirmed persistence. | declined (proposed) | Memory is the harness's; `engram:persistent-memory`'s condition has not held. |
| `engram:pr-body-from-template` | The PR skill points at the repo's PR template instead of duplicating it. | declined (proposed) | `skills/pr/SKILL.md` is the one template and `review-record` parses it. |
| `engram:local-is-not-ci` | Record checks actually run; local success is not a hosted CI pass. | declined (proposed) | `pstack:reply-evidence` and `skills/babysit-pr/SKILL.md`. |
