# Contract

The project files a shared skill may read, and the question each one answers. A shared skill names
a project file only from this table; everything else it needs comes from a file here, or from a
project's own skill. `tests/lint_skills.py` holds every skill to the table.

A project meets the contract when every **required** file exists and has the sections its row
names. An **optional** file is followed when it exists and skipped when it does not. A section named § X is a `##` heading reading X.

| File                                | Need     | Answers                                                                                                                                                                                                                                                    |
| ----------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AGENTS.md`                         | required | Where each project rule lives: coding standards, code language, test-support files, the domain docs, the docs layout. The router every session loads.                                                                                                     |
| `GLOSSARY.md`                       | required | The domain terms: one entry per term, the code identifier and the word a user reads; a phrase the user says that no identifier carries is a spoken term.                                                                                                                                                                      |
| `docs/adr/`                         | optional | The decisions in force and their reasons, one numbered file each, with a `Governs:` line naming the code each shapes. Created with the first ADR; a superseded one is deleted.                                                                                                                                                                     |
| `.capy/setup.json`                  | optional | How a thread's machine is set up, when the project keeps its Setup in the repo: the initialize and refresh scripts. The initialize script clones `leomontigatti/agent-workflow`, and a startup entry runs that clone's `update.sh` on every boot: it checks out the newest release tag and runs `install.sh`, which is how a skill finds `~/.agents/workflow`. |
| `docs/agents/validation.md`         | required | Which commands check code. § Before committing: the list a session runs once at the end. § As you go (optional): the fast check for one green slice. § Heavy (optional): the commands of § Before committing that CI runs instead of the session, and the workflow and job that run them (`skills/implement/HEAVY.md`).                                                                                                     |
| `docs/agents/verification.md`       | required | How to prove behaviour a user can see: § Launch, § Doctor, § Drive, § Evidence, § Cleanup, and § Feature map (which flow proves which area). § Cleanup names the command that stops what § Launch started. § Drive names the browser CLI that clicks and takes evidence; a project without one drives with the browser on the thread's machine (`skills/implement/PREVIEW.md`). § Prototype (optional): how the project's gates beyond lint and types treat a `prototype/` branch (`skills/prototype/SKILL.md`). |
| `docs/agents/review.md`             | required | § Full review: the areas that send a diff to the full review. § Always ask: the areas where a finding is the user's call. § Hotspots: where the code has been hurt, and who acts concurrently and how often, for the correctness brief and the weighing of a race. § Breadth: the project's breadth items. § One-way doors. Its `review-paths` block lists the paths of each full-review area and of changes with no runtime behaviour, read by the shared `review.py`. |
| `docs/agents/issue-tracker.md`      | required | How the tracker expresses work: § Conventions, § Labels, § Closing an issue, § Ticket operations, § PRD workflow, § Wayfinding operations, § Research tickets.                                                                                           |
| `docs/agents/pull-requests.md`      | required | The command that checks a PR title, if any, and the project's base-branch rules. The title rule, stacking and who merges are global (the `pr` and `babysit-pr` skills).                                                                                                                                       |
| `docs/agents/tdd-*.md`              | optional | Test-first notes for one kind of code (`tdd-db.md`, `tdd-frontend.md`, `tdd-odoo.md`). The `tdd` skill follows every one whose kind the change touches.                                                                                                |
| `docs/agents/research.md`           | optional | The primary sources the `research` agent prefers for this stack, and where the pinned versions are.                                                                                                                                                      |

## Sections

A section named here is a heading of that name in the file (`## Before committing`). A skill points
at it as "`docs/agents/validation.md` § Before committing", so a project may add sections freely
and rename only these.

## Extension points

A shared skill that needs project detail it cannot state generically reads an optional file:
"if `docs/agents/<x>.md` exists, follow it too". The detail lives there, never in a fork of the
skill. A project-specific skill lives in the project's `.agents/skills/` under a name no shared
skill uses.

## Changing the contract

Adding a row makes a file every project must write, so it goes with a PR here that names the file
each project adds, and with the lint's table updated in the same change. A file a skill needs only
some of the time is an optional row.
