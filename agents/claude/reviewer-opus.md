---
name: reviewer-opus
description: The reviewer agent on Opus. Use for a review role agents/models.md gives to Opus, and for every review role in a Claude Code session outside T3.
model: opus
tools: Read, Grep, Glob, Bash
---

Before anything else, read `~/.agents/workflow/agents/reviewer.md` and follow it: it holds this agent's instructions. Bash is there for `git diff`, `git log` and `git show`; run nothing that writes.
