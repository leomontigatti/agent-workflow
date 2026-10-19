#!/usr/bin/env python3
"""Lint the shared skills and agent briefs against the rules a shared file must keep.

Usage: python3 -I tests/lint_skills.py

Fails (exit 1) when:

- a shared file names a project command (`pnpm`, `uv`, `just`, `vp`, ...);
- a shared file names a project file that `contract.md` does not list;
- a relative Markdown link, or its anchor, does not resolve, anywhere in the repo;
- a skill's frontmatter `name:` is not its folder name, which the Skill tool calls it by;
- a shared file mentions an upstream repo (`upstreams/sources.json`, plus the former sources
  listed below).

"Shared file" means everything under `skills/` and `agents/`. Paths are checked in inline code and
link targets; commands in inline code and fenced blocks, and the unambiguous ones in prose too.
"""

import fnmatch
import json
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
SHARED_DIRS = ["skills", "agents"]
INSTALL_ROOT = "~/.agents/workflow/"

# Commands that only exist in some projects. In code they are matched at a command position; in
# prose only the ones that are never an English word.
PROJECT_COMMANDS = ["pnpm", "npm", "npx", "yarn", "bun", "bunx", "uv", "uvx", "vp", "just", "pip",
                    "pipx", "poetry", "make", "cargo", "vitest", "jest", "playwright-cli",
                    "playwright", "drizzle-kit", "tsc", "docker", "odoo", "pytest"]
PROSE_COMMANDS = ["pnpm", "npx", "yarn", "uvx", "vitest", "playwright-cli", "drizzle-kit",
                  "uv run", "vp check", "vp fmt"]

# Former sources that are not watched any more but must not reappear either.
FORMER_UPSTREAMS = ["course-video-manager", "humanlayer", "show-me", "do-work", "dexhorthy"]

# Paths that are harness or tool locations, not project files.
ALLOWED_PATHS = {".claude/worktrees/", "CLAUDE.md", "pingdotgg/t3code"}

# A bare file name counts when it is written like a project root file: CONTEXT.md, CODING_STANDARDS.md.
ROOT_DOC = re.compile(r"^[A-Z][A-Z0-9_-]*\.md$")
BARE_PROJECT_FILES = {"justfile", "Makefile", "Dockerfile", "package.json", "pyproject.toml"}
REL_PATH = re.compile(r"^\.?[\w-]+(/[\w.*<>{}…-]*)+$")
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
INLINE_CODE = re.compile(r"`([^`\n]+)`")
FENCE = re.compile(r"^\s*(```|~~~)")

problems = []


def report(path, line, msg):
    problems.append(f"{os.path.relpath(path, ROOT)}:{line}: {msg}")


def contract_entries():
    entries = []
    for line in open(os.path.join(ROOT, "contract.md"), encoding="utf-8"):
        if line.startswith("| `"):
            entries.append(line.split("`")[1])
    return entries


def upstream_names():
    data = json.load(open(os.path.join(ROOT, "upstreams", "sources.json"), encoding="utf-8"))
    names = set(FORMER_UPSTREAMS)
    for s in data["sources"]:
        names.add(s["repo"])
        names.add(s["id"])
        owner = s["repo"].split("/")[0]
        if len(owner) > 6:  # a short owner ("cursor") is an ordinary word; the full repo covers it
            names.add(owner)
    return sorted(names)


def split_code(lines):
    """Yield (lineno, text, in_fence) for each line."""
    in_fence = False
    for i, line in enumerate(lines, 1):
        if FENCE.match(line):
            in_fence = not in_fence
            yield i, line, True
            continue
        yield i, line, in_fence


def slug(heading):
    s = heading.strip().lower()
    s = re.sub(r"[`*_]", "", s)
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


def anchors(path):
    out, in_fence = set(), False
    for line in open(path, encoding="utf-8"):
        if FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and line.startswith("#"):
            out.add(slug(line.lstrip("#")))
    return out


def check_links(path, lines):
    base = os.path.dirname(path)
    for i, line, in_fence in split_code(lines):
        if in_fence:
            continue
        for target in LINK.findall(INLINE_CODE.sub("", line)):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target):
                continue
            file_part, _, anchor = target.partition("#")
            dest = os.path.normpath(os.path.join(base, file_part)) if file_part else path
            if not os.path.exists(dest):
                report(path, i, f"broken link: {target}")
            elif anchor and dest.endswith(".md") and anchor not in anchors(dest):
                report(path, i, f"broken anchor: {target}")


def resolves(token, path):
    skill_dir = os.path.join(ROOT, *os.path.relpath(path, ROOT).split(os.sep)[:2])
    if token.startswith(INSTALL_ROOT):
        return os.path.exists(os.path.join(ROOT, token[len(INSTALL_ROOT):]))
    for base in (os.path.dirname(path), skill_dir, os.path.join(ROOT, "skills"), ROOT):
        if os.path.exists(os.path.normpath(os.path.join(base, token))):
            return True
    if "/" not in token:  # a bare name: a file anywhere in the same skill
        return any(token in files for _, _, files in os.walk(skill_dir))
    return False


def in_contract(token, contract):
    for entry in contract:
        if token == entry or fnmatch.fnmatch(token, entry):
            return True
        if entry.endswith("/") and token.startswith(entry):
            return True
        if token.endswith("/") and entry.startswith(token):
            return True
    return False


def check_paths(path, lines, contract):
    for i, line, in_fence in split_code(lines):
        if in_fence:
            continue
        tokens = INLINE_CODE.findall(line) + [t.partition("#")[0] for t in LINK.findall(line)]
        for token in tokens:
            token = token.strip()
            if not token or " " in token or token in ALLOWED_PATHS:
                continue
            if token.startswith(INSTALL_ROOT):
                if "<" not in token and not resolves(token, path):
                    report(path, i, f"installed path not in this repo: {token}")
                continue
            is_path = REL_PATH.match(token) and not re.match(r"^\.?[\w-]+/$", token)
            is_file = ROOT_DOC.match(token) or token in BARE_PROJECT_FILES
            if not (is_path or is_file):
                continue
            if re.search(r"[<{…]", token) and not in_contract(token, contract):
                continue  # a placeholder, not a path
            if in_contract(token, contract) or resolves(token, path):
                continue
            report(path, i, f"project file outside contract.md: {token}")


def check_commands(path, lines):
    code_cmd = re.compile(r"(?:^|[\s;&|(]|\$\()(" + "|".join(map(re.escape, PROJECT_COMMANDS)) + r")(?=\s|$)")
    prose_cmd = re.compile(r"\b(" + "|".join(map(re.escape, PROSE_COMMANDS)) + r")\b")
    for i, line, in_fence in split_code(lines):
        if in_fence:
            for m in code_cmd.finditer(line):
                report(path, i, f"project command in a code block: {m.group(1)}")
            continue
        for code in INLINE_CODE.findall(line):
            for m in code_cmd.finditer(code):
                report(path, i, f"project command in inline code: {m.group(1)}")
        for m in prose_cmd.finditer(INLINE_CODE.sub("", line)):
            report(path, i, f"project command in prose: {m.group(1)}")


def check_upstreams(path, text, names):
    pattern = re.compile(r"(?<![\w-])(" + "|".join(map(re.escape, names)) + r")(?![\w-])", re.I)
    for i, line in enumerate(text.splitlines(), 1):
        for m in pattern.finditer(line):
            report(path, i, f"mentions an upstream: {m.group(1)}")


FRONT_NAME = re.compile(r"""^name:\s*(?:"([^"]*)"|'([^']*)'|([^\s#]+))""")


def check_skill_names():
    for d in sorted(os.listdir(os.path.join(ROOT, "skills"))):
        path = os.path.join(ROOT, "skills", d, "SKILL.md")
        if not os.path.isfile(path):
            continue
        lines = open(path, encoding="utf-8").read().splitlines()
        front = []
        if lines and lines[0] == "---":
            for line in lines[1:]:
                if line == "---":
                    break
                front.append(line)
        for n, line in enumerate(front, 2):
            m = FRONT_NAME.match(line)
            if m:
                name = next(g for g in m.groups() if g is not None)
                if name != d:
                    report(path, n, f'skill name "{name}" does not match its folder "{d}"')
                break
        else:
            report(path, 1, "skill has no name: line in its frontmatter")


def walk(dirs, exts):
    for d in dirs:
        for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, d)):
            dirnames[:] = [n for n in dirnames if not n.startswith(".") and n != "__pycache__"]
            for name in sorted(filenames):
                if name.endswith(exts):
                    yield os.path.join(dirpath, name)


def main():
    contract = contract_entries()
    names = upstream_names()

    for path in walk(["."], (".md",)):
        if f"{os.sep}.git{os.sep}" in path:
            continue
        check_links(path, open(path, encoding="utf-8").read().splitlines())

    for path in walk(SHARED_DIRS, (".md", ".toml", ".yaml", ".yml", ".py", ".sh")):
        text = open(path, encoding="utf-8").read()
        check_upstreams(path, text, names)
        if path.endswith(".md"):
            lines = text.splitlines()
            check_paths(path, lines, contract)
            check_commands(path, lines)

    check_skill_names()

    for p in problems:
        print(p)
    if problems:
        print(f"\n{len(problems)} problem(s)")
        return 1
    print("lint: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
