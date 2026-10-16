# agent-workflow: guide for coding agents

The one global copy of the agent workflow every project shares: its skills, agent briefs, hooks
and the contract between them and a project. A change here reaches every project at once, the
moment it merges, so each change goes through a PR and nothing is committed to `main` directly.

## What lives where

- `skills/<name>/`: the shared skills, one per folder. Each holds a procedure, never a project
  fact.
- [`contract.md`](contract.md): the project files a shared skill may read, and the question each
  answers. A skill reaches project detail only through it.
- `agents/`: the reviewer, research and implementer briefs, and [`models.md`](agents/models.md),
  the one table of which model each role runs on. `agents/claude/` and `agents/codex/` are the
  thin harness wrappers.
- `hooks/`: the hooks that depend on no project.
- [`t3-dependencies.md`](t3-dependencies.md): what the shared files assume about T3 Code.
- `upstreams/`: the watched upstream repos, their watermarks, and every verdict on an idea from
  them ([`decisions.md`](upstreams/decisions.md)). Upstream URLs live there and in `NOTICE`
  only.
- [`install.sh`](install.sh): links all of it where Claude Code and Codex read it, through the
  stable path `~/.agents/workflow`, which is how a skill or wrapper names a file here.

## Every change

- **Branch and PR.** Work in the thread's worktree, on a `feat/`, `fix/`, `docs/` or `chore/`
  branch, and open a PR against `main`. The PR body names the projects whose behaviour changes and
  what each must add or rename to keep meeting the contract.
- **Write for agents.** Every skill, brief and doc here is read by an agent: call the Skill tool
  with "writing-for-agents" before editing one.
- **Tag a release** after merging a change to `actions/` or to what an action runs
  (`skills/implement/scripts/review.py`): `vX.Y.Z` on the merge commit, minor for a new rule, major
  when a project must change its workflow. Projects pin the action to a tag
  ([its README](actions/review-record/README.md)).
- **Run the lint**: `python3 -I tests/lint_skills.py`. CI runs it with `tests/test_lint.sh` and
  `tests/test_install.sh`. Run `install.sh` only when the user asks; the install test uses a
  throwaway `HOME`.

## Changing a shared skill

- **A project fact goes to the project.** When a skill needs a command, a path, a domain area or
  a tool that differs between projects, point at the contract file that answers it
  (`docs/agents/validation.md` § Before committing), never name it. Name contract files in inline
  code, not as links: links resolve only inside this repo.
- **Detail some projects need is an extension point**: "if `docs/agents/<x>.md` exists, follow it
  too", added to `contract.md` as an optional row. A skill only one project uses lives in that
  project, under a name no shared skill has.
- **A new required contract file is a breaking change**: the PR lists the file every project must
  write, and lands with the lint's view of the contract (the table in `contract.md`) updated.
- **A model changes in `agents/models.md`**, and in the wrappers in the same commit; nothing else
  names one.
- **A T3 assumption** a change adds or drops is an entry in `t3-dependencies.md`, with its
  **Used by** kept true.
- **An idea taken from an upstream** gets its row in `upstreams/decisions.md`, and its license
  entry in `NOTICE` when text is carried over. The skill itself never names the upstream.
