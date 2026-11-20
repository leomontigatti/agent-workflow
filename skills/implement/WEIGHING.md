# Weighing a race or an edge case

A race the change itself brings in is fixed. A race it only finds, and an edge case it finds or
leaves unguarded in its own code, at any severity, a traced `critical` one included, is weighed on
three things:

- its **likelihood**: who the concurrent actors are (roles and the surfaces they act through), how
  wide the window is (inside one transaction, or between a page load and a submit), and how often
  each side runs, so how often the window actually opens; for an edge case, how often normal use
  produces the input or the stored state that triggers it;
- what a **hit** costs: a **silent** hit (data lost or wrong, and nobody notices) outweighs a
  **loud** one (an error someone sees and retries, with nothing lost or half-written);
- what the **fix** costs: the locks, states and tests it adds, and the deadlocks or races those
  can bring in.

Take the actors and their frequencies from `docs/agents/review.md` § Hotspots, measured the way it
says. Where it names none, read them off the entry points that reach each side (which roles,
which surfaces), and mark it a guess. A guess is grounded when it names a race's two sides and its
window, or what produces an edge case's input or stored state; the likelihood is ungrounded only
when you could not find one of those.

The weighing ends in one of two rulings:

- **Drop**, when the hit is loud and unlikely: it takes two rare actions overlapping (admin-only
  ones, a manual correction), or an input normal use never produces. The ruling is yours. The
  drop is one line in the final report (what it is, why it is unlikely, what the person sees), and
  it ends there, with no ask, issue or question behind it.
- **Ask**, in every other case: a silent hit, a likely one, or an ungrounded likelihood.
  State it in plain words someone outside the code can rule on (what breaks and for whom, how
  likely it is, what the fix costs) with your pick: fix it, park it with the condition that would
  raise its likelihood, or close it as not planned when its hits cost less than its fix. An issue
  for it is opened once the user rules for one; it states all three and the pick, and triage
  decides by `docs/agents/issue-tracker.md` § Labels.
