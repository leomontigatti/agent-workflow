# Validation: agent-workflow

What a session runs before it commits. CI (`.github/workflows/lint.yml`) runs the same commands
and is the merge gate.

## Before committing

```sh
python3 -I tests/lint_skills.py     # every skill, brief and doc; the context budget
tests/test_lint.sh                  # only when tests/lint_skills.py changed
shellcheck install.sh tests/*.sh skills/*/scripts/*.sh   # when a shell file changed
```

Then the test of each script the diff touches, and of each script that imports or calls it: a
changed signature breaks its callers' tests, which no other command here runs.

| Changed                                         | Run                                                      |
| ----------------------------------------------- | -------------------------------------------------------- |
| `skills/implement/scripts/review.py`            | `python3 -I tests/test_review.py`                        |
| `skills/upstream-review/scripts/`               | `python3 -I tests/test_upstreams.py`                     |
| `lib/parts.py`                                  | `python3 -I tests/test_parts.py` and its importers' tests |
| `evals/reviewer-recall/`                        | `python3 -I tests/test_reviewer_recall.py`               |
| `skills/retro/scripts/`                         | `python3 -I tests/test_retro_sessions.py`                |
| `skills/domain-modeling/scripts/`               | `python3 -I tests/test_anchors.py`                       |
| `install.sh`, a skill added or removed          | `tests/test_install.sh` (a throwaway `HOME`)       |

Use `python3`: no `python` is on PATH. A machine without `shellcheck` cannot run the third
command; say so in the PR, since CI will be its first run.

When the lint reports the context budget, follow `AGENTS.md` § Every change: shorten first, and
run `--update-budget` only for growth that earns its load. `--update-budget` rewrites every
entry, so check that the diff of `tests/context-budget.json` holds only the files you changed.
