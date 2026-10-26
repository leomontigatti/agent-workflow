---
name: to-spec
description: "Turn the current conversation into a spec and publish it to the project issue tracker: no interview, just synthesis of what you've already discussed."
disable-model-invocation: true
---

This skill takes the current conversation context and codebase understanding and produces a spec. Do NOT interview the user; just synthesize what you already know.

A spec is for a build too big for one session, split across several: `to-tickets` cuts it into tickets and `implement-spec` builds them. Work one session can finish skips it and goes straight to the `implement` skill: there a spec buys nothing, and its synthesis is one more step where the model can drift from what the user said. When the conversation is about such work, say so and stop.

Read `docs/agents/issue-tracker.md` first: it says how this repo's tracker expresses specs, tickets, sub-issues, blocking and labels.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the spec, and respect any ADRs in the area you're touching.

2. Sketch out the seams at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better - the ideal number is one.

Check with the user that these seams match their expectations.

3. Write the spec using the template below, then publish it as `docs/agents/issue-tracker.md` § Ticket operations says for a PRD, with the label § Labels gives work an agent may pick up.

<spec-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Out of Scope

A description of the things that are out of scope for this spec.

## Further Notes

Any further notes about the feature.

</spec-template>

## A snapshot, not a source

The spec records what was decided when it was written, and stays the one place the reasoning behind the tickets lives while they are built. Nothing keeps it in sync with the code, and the build will teach things it doesn't say. What should outlast the build goes to `GLOSSARY.md` or `docs/adr/` (the `domain-modeling` skill), never into the spec. When the route changes mid-build (a decision replaced, the destination the same), leave the spec's sections as written and append to its body a `## Changed during the build` section: one line per replaced decision or ticket, what replaces it, and why. Close each replaced ticket as `docs/agents/issue-tracker.md` § Closing an issue says for work that will not be done, with a comment naming its replacement, and cut the new tickets with `to-tickets`. The review at the end of `implement-spec` reads the spec whole, so that section is what tells it which decisions and tickets govern. When the destination changes, that is a new spec. Once the PRD's PR merges, the spec is history: the code, its tests, the glossary and the ADRs describe the system.
