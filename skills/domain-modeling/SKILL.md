---
name: domain-modeling
description: Build and sharpen a project's domain model. Use when discussing codebase terminology, writing or editing a GLOSSARY.md, or recording or editing an ADR.
---

# Domain Modeling

Actively build and sharpen the project's domain model as you design. This is the _active_ discipline: challenging terms, inventing edge-case scenarios, and writing the glossary and decisions down the moment they crystallise. (Merely _reading_ `GLOSSARY.md` for vocabulary is not this skill: that's a one-line habit any skill can do. This skill is for when you're changing the model, not just consuming it.)

## File structure

A project has a single context:

```
/
├── GLOSSARY.md      ← the terms
└── docs/
    └── adr/         ← the decisions, one numbered file each
        ├── 0001-….md
        └── 0002-….md
```

`AGENTS.md` routes to any further domain docs (the detailed rules the glossary points at). If no
`docs/adr/` file covers a decision, create the next numbered ADR when it is needed.

An ADR records why; the code says what is. When your output contradicts an ADR, say so rather than
silently overriding it: "Contradicts ADR-0002, but worth reopening because…". When the code
already contradicts one, the code is current: raise the mismatch with the user, who rules which of
the two changes. A reversal is a new ADR, and the one it supersedes is deleted in the same change:
git keeps the record, and a reader finds only decisions in force.

`python3 -I ~/.agents/workflow/skills/domain-modeling/scripts/anchors.py` lists every ADR and
glossary term whose **anchor** has left the code. Run it before relying on either and after
editing one: each `gone:` line is such a mismatch.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `GLOSSARY.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y. Which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account': do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible. Which is right?"

### Update GLOSSARY.md inline

When a term is resolved, update `GLOSSARY.md` right there. Don't batch these up: capture them as they happen. Use the format in [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md).

`GLOSSARY.md` should be totally devoid of implementation details. Do not treat `GLOSSARY.md` as a spec, a scratch pad, or a repository for implementation decisions.

### Offer ADRs sparingly

An ADR is the last resort: a decision that a type, a lint rule or a test can hold lives there,
where a break fails a check. Only offer to create an ADR when all three are true:

1. **Hard to reverse**: the cost of changing your mind later is meaningful
2. **Surprising without context**: a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off**: there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).
