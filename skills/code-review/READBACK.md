# Readback

The review tier for a diff that touches none of the risky areas in step 5 of the `implement`
skill. It catches a diff that does something other than what its author thinks it does, and a new
test that catches no bug. The rest of the standards and the spec are the full review's.

1. Pin the fixed point: the branch point against the base branch. Run `git add -N` on new files,
   confirm the diff (`git diff $(git merge-base <base> HEAD)`, which takes in uncommitted work) is
   non-empty, and note `git log <base>..HEAD --oneline`.
2. Spawn **one** readback reviewer, as [Spawning a reviewer](SKILL.md#spawning-a-reviewer) says,
   with the diff command and the commit list, and this brief, in the same message as the
   correctness axis when the diff changes behaviour (step 5 of `implement`):

   > Read the diff. Restate in plain words what it does, as a reviewer would explain it to the
   > author. Then list anything surprising: behaviour the commit messages do not mention, a
   > change that looks unrelated to the rest, code that contradicts its own comment or name,
   > anything you would ask about before approving. Say "nothing surprising" if there is
   > nothing. Then, for every test case the diff adds or grows, name in one line the bug it
   > catches (the wrong implementation that makes it fail), or flag it as low-signal with the
   > anti-pattern it matches in `~/.agents/workflow/skills/tdd/SKILL.md` § Anti-patterns, or the
   > existing case that already catches its bug, and flag each name that promises a clause its
   > assertions do not check ("Name only what it asserts" in the same skill). End with one line:
   > `Would merge: yes | after fixes | no`. Under 300 words.

3. Report it under `## Readback`, verbatim or lightly cleaned, ending with one line: how many
   surprises and low-signal tests it flagged, and its merge verdict. A low-signal test is a
   finding like any other: deleted or folded into the case it names, or declined with the bug it
   does catch.

When a surprise turns out to touch an area in `docs/agents/review.md` § Full review, a migration,
a `GLOSSARY.md` term or a destructive operational script, the diff was risky after all: run the
full `code-review`.
