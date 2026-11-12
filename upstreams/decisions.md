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

## First look: tstack 7de017b (2026-10-26)

Nine skills for Claude Code and Codex that already lean on T3 (`watch_pull_request`, `delegate_task`). Two ideas were already decided under pstack names: `pstack:watch-pr-script` (its `pr-wait`) and `pstack:verification-skill`. Verdicts marked proposed stand until this review's PR merges.

| Id | Idea | Verdict | Where or why |
| -- | ---- | ------- | ------------ |
| `tstack:watch-rate-limit` | A watch that ended because it could not read the PR: check the GraphQL budget before watching again; read through REST meanwhile. | declined (proposed) | T3 already pauses a watch while GitHub rate-limits it and counts only other failures toward giving up (`isRateLimited` in `apps/server/src/orchestration-v2/PullRequestWatchReactor.ts`, read 2026-10-26). |
| `tstack:merge-base-overlap` | Before merging, a base commit since the merge base that touches the PR's files sends it back to update and wait. | adopted | `skills/babysit-pr/SKILL.md` § 4c. |
| `tstack:review-scope-guard` | Prefer the fix that deletes or narrows code; a true finding outside the PR's goal is declined as out of scope and listed as a follow-up. | adopted | `skills/babysit-pr/triage.md` § The three verbs and `skills/implement/SKILL.md` step 5 (**fix**, **decline**). |
| `tstack:pr-title-says-why` | The PR title names the effect that matters, not the mechanism. | adopted | `skills/pr/SKILL.md` intro. |
| `tstack:secrets-check-before-posting` | Read a PR title, body or comment, and what it quotes, for secrets and private data before posting. | adopted | `skills/pr/SKILL.md` § Rules; `skills/babysit-pr/SKILL.md` § 4. |
| `tstack:agent-comment-attribution` | Every comment an agent posts under the user's account opens with a note naming the model and the user. | adopted | `skills/pr/SKILL.md` § Rules, pointed at from `babysit-pr` § 4, `implement-spec` § 3 and `wayfinder`. Confirmed by the user 2026-10-26. |
| `tstack:modernize` | Revive a stale PR: restate its goal, read the base's changes, choose modernize / rework / close before pushing, `range-diff` after the rebase. | later (proposed) | When PRs sit open past a week; ours merge within a session. |
| `tstack:council` | Three reviewers from three providers loop until all agree. | later (proposed) | The second family paid (reviewer-recall, 2026-10-27); reopen when a third provider is reachable. |
| `tstack:full-send` | Unattended to a merged PR; the request overrides ask-first testing rules. | declined (proposed) | `implement` with `babysit-pr` runs to the merge when it is the agent's; ask-first rules are the project's. |
| `tstack:full-stop` | The same, stopping at ready, auto-merge disabled first. | declined (proposed) | `babysit-pr`'s merge rule stops at READY; nothing of ours enables auto-merge. |
| `tstack:auto-merge-guard` | When the merge is the user's, turn off auto-merge or a merge-queue entry already on the PR before pushing, and check again before each push. | declined (proposed) | Auto-merge on our PRs is only ever turned on by the user, and that is their merge decision; one author per project, so no one else's setting is inherited. Reopen if `takeover` is adopted. |
| `tstack:ask-via-question-tool` | An unattended run asks through the question tool so the thread shows it waits. | declined (proposed) | `babysit-pr` § 5 unwatches, returning the thread to the inbox, and leads with NEEDS YOU. |
| `tstack:sol-loop` | A Sol review loop: blocker / should / nit, 3 rounds (5 for risky areas), a ledger. | declined (proposed) | `implement` step 5's cross-family review and fix round; `babysit-pr`'s three rounds. |
| `tstack:review-scores` | Each reviewer scores out of 10 per round, tabled in the PR body. | declined (proposed) | `## Review` counts findings per axis and `review-record` reads it. |
| `tstack:model-harness-line` | The PR body ends with the model and harness that made it. | declined (proposed) | The harness's attribution and `## Review`'s model per axis. |
| `tstack:takeover` | Finish another's PR or thread, keeping their git credit; the handoff is context, not proof. | declined (proposed) | One author per project; `implement` proves the change itself. |
| `tstack:comment-style` | Comments lead with the conclusion and cite code; resolve only after the reply posts. | declined (proposed) | `skills/babysit-pr/triage.md` demands the SHA or the disproof per reply. |
| `tstack:bot-rules` | Macroscope rule files read first; CodeRabbit advisory, never waited on. | declined (proposed) | A project fact, for `docs/agents/review.md`. |
| `tstack:silent-wake` | A wake that needs nothing ends the turn without a message. | declined (proposed) | A no-op: `babysit-pr` reports only at step 5. |
| `tstack:only-owner-watches` | A delegated child never watches; the parent owns the PR. | declined (proposed) | `skills/babysit-pr/SKILL.md` § 2; T3 refuses it. |
| `tstack:proof-per-fix` | Proof for each review fix before pushing it. | declined (proposed) | `skills/babysit-pr/SKILL.md` § 4. |
| `tstack:pr-body-problem-first` | The PR body opens with the problem in the user's words, not an inventory. | declined (proposed) | `skills/pr/SKILL.md`: the why lives in the issue. |
| `tstack:rest-fallback-pr-create` | When `gh pr create` fails because GitHub's GraphQL budget is spent, open the PR through REST (`gh api repos/{owner}/{repo}/pulls` with the body from a file). | adopted | `skills/pr/SKILL.md` intro. |

## Spec-driven development, researched (2026-10-26)

Is a written spec still worth it as models improve? Read from mattpocock-skills' `docs/engineering/` (which `sources.json` did not watch until now, so these never reached a weekly review), pstack's README, gentle-ai v4.0.0 and Anthropic's Claude Code best practices. They agree: no spec for work one session finishes; a disposable handoff for work split across sessions, thorough in what was decided, with no file paths or code to go stale. `sources.json` now watches that folder as its own source, `mattpocock-docs`, from the commit before it existed, so the next weekly review reads all of it once; an idea there already decided below under `mattpocock-skills:` is the same idea. Verdicts marked proposed stand until this PR merges.

| Id | Idea | Verdict | Where or why |
| -- | ---- | ------- | ------------ |
| `mattpocock-skills:spec-multi-session-only` | A spec only when the build spans several sessions; otherwise go straight to implementation, since the synthesis is one more place to drift. | adopted (proposed) | `skills/to-spec/SKILL.md` intro. |
| `mattpocock-skills:spec-is-snapshot` | The spec is a snapshot nothing keeps in sync; lasting knowledge goes to the glossary and ADRs; a replaced decision is appended to the spec, never edited in; disposable after the work ships. | adopted (proposed) | `skills/to-spec/SKILL.md` § A snapshot, not a source; the tickets a replaced decision touches, `skills/implement-spec/SKILL.md` § Route change. |
| `mattpocock-skills:implement-spec-one-review` | The parallel run's output is a draft that one final review completes; no second broad review. | declined (proposed) | Already there: `skills/implement-spec/SKILL.md` § 4 (draft PR, one review, "no second broad review"). |
| `mattpocock-skills:deterministic-afk-loop` | For truly unattended runs, a script or CI loop orchestrates more cheaply and reliably than an agent. | later (proposed) | When `implement-spec` runs overnight unattended and its agent orchestration shows up in a retro as a cost or a failure. |
| `pstack:no-planning-default` | Planning is not the default; "the best spec is code"; a checked plan only for multi-phase work. | declined (proposed) | Already our shape: `implement` is the default and every spec skill is user-invoked (`disable-model-invocation`). |
| `gentle-ai:odd-feature-document` | One feature document per substantial change (the user's words verbatim, tasks, log) replaces a named SDD workflow. | declined (proposed) | Our spec issue and its tickets do the same on the project's tracker, which `implement-spec` and `review-record` already read. |

## Fold subagents into one agent with skills, from Anthropic (2026-10-26)

Anthropic's Applied AI guide "Building agents: When to fold subagents into your main agent loop" (2026-10-22), reached through a video summary of it. Anthropic is not a watched source, so these rows carry `anthropic:`. The guide folds specialists that chain on each other's output into one agent with skills, and keeps a subagent for verification, parallel work in a fresh context, context bloat, and a tool choice one agent gets wrong. Its evidence is one customer's 2x speedup, with no sample sizes. Verdicts marked proposed stand until this PR merges.

| Id | Idea | Verdict | Where or why |
| -- | ---- | ------- | ------------ |
| `anthropic:fold-subagents` | Fold subagents into the main loop as skills; keep one only when the folded version scores worse. | declined (proposed) | No role in `agents/models.md` chains into another specialist, the shape the guide folds. The reviewers are verification from the other family; Research, Miners and Design runners are parallel reads in a fresh context; Codebase mapping keeps file dumps out of the session's context. The Implementer is the exception: it splits writing across sessions, the case the guide warns about. We keep it because a spec is by definition too big for one session, and `implement-spec` § 4's one review of the whole spec is where a misfit between tickets would show. Reopen when that review finds tickets that don't fit together. |
| `anthropic:eval-before-fold` | Build a small end-to-end eval (about 10 golden tasks, each run twice) before changing the harness. | later (proposed) | When a change proposes folding or splitting an agent role. Until then the `## Review` records on our PRs show what each reviewer catches. |
| `anthropic:no-op-sweep` | Read every always-loaded line and cut what the current model does without being told. | adopted (proposed) | The no-op rule already lives in `skills/writing-for-agents/SKILL.md` § Pruning; adopted here is one sweep of every shared skill with it, in its own PR (`chore/skill-no-op-sweep`). |
| `anthropic:shim-firing-log` | Log each time a guardrail fires; propose deleting one that has stopped firing. From a talk the video cites, not from the guide. | later | Only `hooks/` could log their firings, three of them, and the two blockers guard rare, costly mistakes, where a silent month proves nothing. When `hooks/` holds about five guardrails, or a retro finds one blocking work it should not: each appends a line to a log when it fires, and `retro` names one silent for a month. |

## Weekly review (2026-11-02): pstack v0.15.36, mattpocock-skills 4ae2317, mattpocock-docs 4ae2317, gentle-ai 5b2168b, engram d33a14a, tstack 1085050

Verdicts marked proposed stand until this review's PR merges; the user approved the eight adopted ones on 2026-11-02. Already decided, so no row: from pstack, the Orchestrate rewrite (`pstack:orch-swarm-loop`), the cross-judge from another family (`pstack:family-diversity`), blocking only on a shown problem (`tstack:review-scope-guard`), no verifier for wording (`pstack:rereview-by-delta`), rebasing for a concurrent change (`tstack:merge-base-overlap`), the statechart rewrite (`pstack:statechart`) and the video's subtitles (`pstack:ketchup-video`); from the rest, `mattpocock-skills:dated-commit-cited-wiki`, `pstack:router-mode`, `mattpocock-skills:implement-spec-one-review`, `mattpocock-skills:deterministic-afk-loop`, `mattpocock-skills:spec-multi-session-only`, `mattpocock-skills:spec-is-snapshot` and `tstack:full-stop`.

| Id | Idea | Verdict | Where or why |
| -- | ---- | ------- | ------------ |
| `mattpocock-docs:review-needs-committed-diff` | A three-dot diff leaves out uncommitted work, which `implement` step 5 reviews. | adopted | `skills/code-review/SKILL.md` § 1 and `skills/code-review/READBACK.md` (#67). |
| `mattpocock-skills:fresh-context-subagents` | Every subagent starts fresh, never as a fork of the parent. | adopted | `agents/models.md` § Reaching each model` (#68). |
| `mattpocock-docs:criteria-can-fail` | Name what would show each acceptance criterion false, and confirm it fails at the starting commit. | adopted | `skills/to-tickets/SKILL.md` § 4` (#69). |
| `mattpocock-docs:worktree-untracked-test-skip` | A test skipped in a worktree for want of untracked material is no pass. | adopted | `agents/implementer.md` step 2` (#70). |
| `mattpocock-docs:grilling-ungrillable-to-prototype` | A question talk cannot settle goes to a prototype. | adopted | `skills/grilling/SKILL.md` (#71). |
| `mattpocock-docs:handoff-downgrade-unverified` | Mark every unchecked claim in a handoff as unverified. | adopted | `skills/handoff/SKILL.md` (#72). |
| `mattpocock-docs:wayfinder-notes-exemption-guard` | Only the user writes or widens the map's "carry execution" override. | adopted | `skills/wayfinder/SKILL.md` § Plan, don't do` (#73). |
| `pstack:decide-before-measure` | Write the deciding result and the noise floor before the first run. | adopted | `skills/diagnosing-bugs/SKILL.md` § Perf branch` (#74). |
| `pstack:goal-first` | Restate the user's goal in the first message, briefs, PRs and final reports. | later (proposed) | When a retro finds a session that built the wrong thing from a misread request. |
| `pstack:interrogate-proven-findings` | Adversaries prove each finding with a run; only what a rerun confirms survives. | later (proposed) | When a retro finds false findings costing review rounds; `implement` step 5 verifies at the caller. |
| `pstack:pilot-unit` | Take one unit through the whole path before fanning out. | later (proposed) | A spec with about ten near-identical tickets. |
| `pstack:retry-by-cause` | Retry a failed worker by the failure's cause; two retries, then replan. | later (proposed) | When `implement-spec` loses a child to something other than `blocked`. |
| `mattpocock-skills:software-factory` | A glossary and product surveys for ticket-driven runs on remote infrastructure. | later (proposed) | Same condition as `mattpocock-skills:deterministic-afk-loop`. |
| `mattpocock-docs:spec-search-tracker` | Search the tracker for overlaps before writing a spec. | later (proposed) | When a spec turns out to duplicate a filed issue. |
| `mattpocock-docs:wayfinder-wrong-decision-reopen` | Challenge a closed decision found wrong instead of designing around it. | later (proposed) | When a retro finds a map built around a bad decision. |
| `gentle-ai:codex-home` | Honour a validated `CODEX_HOME` when writing Codex config. | later (proposed) | When a machine sets `CODEX_HOME`; `install.sh` writes `$HOME/.codex`. |
| `pstack:model-slug-fallback-chain` | Walk a chain of fallbacks when a slug is rejected. | declined (proposed) | `agents/models.md` § Reaching each model fixes the table instead. |
| `pstack:push-each-unit` | Push every finished unit, assuming the VM dies. | declined (proposed) | Our worktrees are local; the orchestrator owns the push. |
| `pstack:background-steers` | Send steers and resumes in the background. | declined (proposed) | T3 wakes the parent; a later round is a new `delegate_task`. |
| `mattpocock-skills:implement-spec-fresh-per-ticket` | A fresh implementer per ticket and for the fixes. | declined (proposed) | Already `skills/implement-spec/SKILL.md` steps 2 and 4. |
| `mattpocock-skills:gh-close-comment-drops` | `gh issue close --comment` loses the comment on a closed issue. | declined (proposed) | A project fact, for `docs/agents/issue-tracker.md`. |
| `mattpocock-skills:file-into-own-repo` | Check the target repo before the first `gh issue create`. | declined (proposed) | One author per project, no forks. |
| `mattpocock-skills:setup-reachable-repo` | The setup skill wires up a remote and renames `CONTEXT.md`. | declined (proposed) | We have no setup skill; `contract.md` is the setup. |
| `mattpocock-skills:retro-sampling` | A coordinator runs a retro on one session in five. | declined (proposed) | `retro` reads the whole window; we have no standing coordinator. |
| `tstack:fix-known-before-review` | Address known issues before a council audit. | declined (proposed) | `skills/implement/SKILL.md` validates at step 3, before review at step 5. |
| `gentle-ai:repo-scoped-pr-policy` | A repo's contribution gates apply only to that repo. | declined (proposed) | `contract.md` keeps such rules in the project. |
| `mattpocock-docs:reviewer-no-fanout` | A reviewer spawns nothing. | declined (proposed) | The wrappers give it no spawn tool; T3 tells a child to do its own work. |
| `mattpocock-docs:review-is-leads-not-loop` | Do not rerun a review until clean. | declined (proposed) | `skills/implement/SKILL.md` § Fix round reviews the fixes alone. |
| `mattpocock-docs:spec-tickets-one-window` | No clear or compact between `to-spec` and `to-tickets`. | declined (proposed) | `to-tickets` reads the published issue. |
| `mattpocock-docs:retro-no-guardrail-finding` | Report a repo with no checks as a finding. | declined (proposed) | `docs/agents/validation.md` is a required contract file. |
| `mattpocock-docs:tdd-browser-tests-last` | Browser tests come after the behaviour works. | declined (proposed) | A project fact, for `docs/agents/tdd-*.md`. |
| `mattpocock-docs:prototype-one-sitting` | A prototype still in progress a day later was too big. | declined (proposed) | A rule of thumb no step acts on. |
| `mattpocock-docs:grilling-scope-too-big-split` | A very long grilling means the scope is too big. | declined (proposed) | `wayfinder` and `to-tickets` own splitting. |
| `mattpocock-docs:handoff-report-path-not-durable` | Print the handoff's path and warn that temp is not durable. | declined (proposed) | Our sessions hand off in T3 threads, within the same machine. |
| `mattpocock-docs:handoff-only-when-travelling` | `/compact` unless something is travelling. | declined (proposed) | `handoff` is user-invoked, so the user is already choosing. |
| `mattpocock-docs:wayfinder-prototype-choice-is-human` | The human picks the prototype variant. | declined (proposed) | `skills/wayfinder/SKILL.md` § Ticket Types. |
| `mattpocock-docs:wayfinder-bounded-destination` | Scope the map to an epic. | declined (proposed) | An upstream failure report with no observed case of ours. |
| `mattpocock-docs:wayfinder-cleared-map-to-spec` | A cleared map points at `to-spec`. | declined (proposed) | A cleared map can end in a one-session change, which needs no spec. |

## Cross-project changes from one home repo (2026-11-11)

| Id | Idea | Verdict | Where or why |
| -- | ---- | ------- | ------------ |
| `mattpocock-skills:home-repo` | Run every agent from one home repo that holds the skills and steering files and has the other repos cloned inside it, so one session makes a sweeping change across repos. | adopted | Adapted: the shared half is already this repo, installed globally; `skills/fan-out/SKILL.md` has a coordinator thread launch one thread per project instead. Agents still run per project, since worktrees, `t3.json` setup, each project's contract and its PR all hang off the project. |

## Choosing a model per task, from Anthropic (2026-11-11)

The guide "Which Claude model should you build with?" on claude.dev (2026-11-09), reached through a post that asks a session to audit its setup against it and a third-party skill that condenses it. The guide speaks as Anthropic, which is not a watched source, so these rows carry `anthropic:`; we did not confirm who owns the site. Its numbers are Anthropic's own benchmark runs, none on our work. Verdicts marked proposed stand until this PR merges.

| Id | Idea | Verdict | Where or why |
| -- | ---- | ------- | ------------ |
| `anthropic:escalation-order` | When a model falls short: first make sure it can verify its own work, then raise effort one level, then move to the next model up at a lower effort; past high, one more effort level can cost as much as the bigger model. | adopted (proposed) | `agents/models.md` § The rule, the ladder. Our one measurement fits rung 3's lower effort and warns about its price: Fable at low matched Opus at medium on reviewer recall (20 and 19 of 30, 2026-11-11) at about twice the cost per review. |
| `anthropic:task-model-table` | A task-to-model table (Haiku for search and extraction, Sonnet for scoped coding and review, Opus for everyday engineering, Fable for migrations and leading subagents), loaded as a skill before every subagent spawn. | declined (proposed) | `agents/models.md` already maps each role to a model, from our own evals, and they disagree with the table: it puts review on Sonnet, where `evals/reviewer-recall` backs Opus and Sol. A second table loaded in every session would be a second source of truth. |
| `anthropic:explore-on-haiku` | Define a subagent named `Explore` with `model: haiku`, since the built-in one now runs on the session's model. | declined (proposed) | A harness setting already does it wider: `CLAUDE_CODE_SUBAGENT_MODEL` puts every subagent with no model on the light one, and every role that needs more names its model. Reopen if `install.sh` starts to own Claude settings. |


## Hill-Climb, a scored keep-or-undo loop (2026-11-11)

The skill and script at github.com/Bil0000/Hill-Climb (MIT), read at `551c997` on the user's request: its README and `SKILL.md`, not its script. It is not a watched source, so these rows carry `hill-climb:`. The user approved the three adopted rows on 2026-11-11; verdicts marked proposed stand until this PR merges.

| Id | Idea | Verdict | Where or why |
| -- | ---- | ------- | ------------ |
| `hill-climb:count-over-clock` | Score speed by a count of the work behind the time; when no count moves with the slowdown, time it and run old and new code in turns so the machine's load falls on both. | adopted | `skills/diagnosing-bugs/SKILL.md` § Perf branch. The minimum gain above the drift was already there, as `pstack:decide-before-measure`'s noise floor. |
| `hill-climb:guess-the-gain` | Write the expected effect of a change before measuring it; a guess far off means the model of the code is wrong, so profile before the next step. | adopted | `skills/diagnosing-bugs/SKILL.md` § Perf branch. |
| `hill-climb:weakened-test` | A step that edits the test it must pass is not a win. | adopted | Adapted: we lock nothing, the correctness reviewer reports it. `skills/code-review/CORRECTNESS.md`, the brief's list. |
| `hill-climb:scored-loop` | A script owns the score: each small change is committed when a locked check improves and the guards pass, and reset otherwise, on a branch of its own with its state on disk. | later (proposed) | Our work is mostly tickets judged against a spec, not a number, and the skill brings its own card, report, branch scheme and model tiers, which `implement`, `pr` and `agents/models.md` own. Reopen when a project has a goal of many scored steps (a slow suite, a bundle size, an audit of a dozen findings): try it there as a project skill first. |
| `hill-climb:holdout` | Cases the loop never trains on, run at the bar; a flat holdout under a rising score is overfitting. | declined (proposed) | Only a long scored loop overfits its check; we run none. Rides on `hill-climb:scored-loop`. |
| `hill-climb:check-kits` | Save each check, its guards and notes as a kit any repo can restore. | declined (proposed) | A second store of project detail outside the repo; a project's checks live in its `docs/agents/validation.md` and `docs/agents/verification.md`. |
| `hill-climb:plateau-review` | After five steps with no gain, stop and find what blocks progress before another step. | declined (proposed) | The trigger counts the steps of a loop we do not run. Rides on `hill-climb:scored-loop`. |
