<img src="assets/icon.svg" width="64" height="64" alt="">

# agent-workflow

The shared agent workflow for our projects, in one copy: skills and agent briefs. It runs on
Capy, where each thread has its own machine: a project's Setup installs it
on every boot, a session reads each skill by path from `~/.agents/skills`, and every role is a subagent
started with the model id [`agents/models.md`](agents/models.md) gives it. Each project keeps only
its own facts, in the files [`contract.md`](contract.md) lists, and its own project-only skills.

- How to change it: [`AGENTS.md`](AGENTS.md).
- How it is installed: a project's Setup runs [`update.sh`](update.sh) on every boot, which checks out the
  newest release tag and runs [`install.sh`](install.sh) (`--check` reports drift).
- Licensing of the parts derived from other work: [`NOTICE`](NOTICE).
