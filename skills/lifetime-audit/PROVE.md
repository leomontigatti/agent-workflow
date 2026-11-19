# Lifetime prover

The brief for one prover of the `lifetime-audit` skill. Your task gives a checkout of the audited
commit that is yours to write in, and one claim: where the bug is, the sequence that triggers it,
and what goes wrong. You get the claim and not the reasoning behind it, so the test is yours.

1. Read the code the claim names, and the project's test layout and helpers (`AGENTS.md` routes to
   them, and to `docs/agents/tdd-*.md` for the kind of code it is).
2. Write the smallest test that drives the code through its public entry points into the claimed
   sequence and asserts the behaviour that should hold. Control the ordering yourself: hold a
   response back with a promise you resolve, fake the timers, run the two writes in the order the
   claim names. A test that only asserts a flag it set itself proves nothing.
3. Run that one test file, with the command `docs/agents/validation.md` § As you go names (or the
   project's test runner, which `AGENTS.md` routes to). Give anything that might not finish a time
   limit.
4. When it goes **red** on the assertion, follow the same sequence to the backstop the claim names
   (the save, the write) and record what the user ends up with. Then make the smallest fix on your
   checkout and check that the test turns green with it.

Answer exactly one of:

- `demonstrated`: red on the current code. Give the test's final text, the failing assertion's
  output, the backstop, and the fix with its green run.
- `confirmed-by-reading`: the sequence needs what a test here cannot drive (a real browser, a
  device, two processes). Say what blocks it, and the test that would reproduce it elsewhere.
- `rejected`: the test stays green, or the sequence cannot happen; say which, and why.

Run each test in the foreground and wait for it to finish; your final message is the verdict,
never a promise to report later. Your machine is throwaway and the audit
cannot read it: push nothing, and put everything the audit needs (the test, the fix as a diff)
in the report. Report as your final message, under 500 words, with the test
text in a code block.
