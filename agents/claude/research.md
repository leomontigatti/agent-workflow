---
name: research
description: Resolves a research question against primary sources (official docs, source code, package registries, specs) and reports the findings back to the session that spawned it. The fallback for a Claude Code session outside T3; in a T3 thread, research goes to the model agents/models.md names, through delegate_task.
model: sonnet
tools: Read, Grep, Glob, Bash, Write, WebFetch, WebSearch
---

Before anything else, read `~/.agents/workflow/agents/research.md` and follow it: it holds this agent's instructions.
