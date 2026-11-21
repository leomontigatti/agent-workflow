#!/usr/bin/env python3
"""The review tier of a diff, and the check that a PR records the review its tier needs.

Usage, from a project checkout:
  python3 -I review.py tier [base]          the tier of everything since base (default: the
                                            remote default branch), uncommitted files included,
                                            then each reviewer's model id, reasoning mode and
                                            brief from agents/models.md, per author family
  python3 -I review.py check --pr <n>       check PR <n>'s `## Review` record
  python3 -I review.py check --body <file> [--base <ref>]
                                            the same for a body not pushed yet, against HEAD and
                                            its merge-base with the remote default branch
  python3 -I review.py check                the same, from PR_BODY, BASE_SHA, HEAD_SHA and
                                            PR_AUTHOR in the environment (CI)

The tier comes from the changed paths and the project's `docs/agents/review.md`, whose
`review-paths` block lists them:

    ```review-paths
    full money: ^app/lib/(finances|prices)/
    full migration: ^app/db/migrations/
    quiet: ^\\.coderabbit\\.yaml$
    ```

- `full <area>: <regex>`: a changed path that matches sends the diff to the full tier.
- `quiet: <regex>`: a path that changes no runtime behaviour, beside the defaults below. A diff
  made only of quiet paths keeps the readback alone.

A `readback+correctness` diff of at most 30 changed lines outside the quiet paths is **small**:
`tier` says so, and names the correctness axis alone. The record keeps its readback line, as
`skipped, small diff`, which the check passes with a warning.

The full tier needs correctness from both model families, Opus and Sol; `both-families`, the line
that once turned this on, is still read and changes nothing.

The record is the `pr` skill's `## Review` section: `Tier: <tier>, reviewed <sha>`, then one
`- <axis> (<model>): <outcome>` line per reviewer. The agent writes it, so it proves nothing on its
own; what the check buys is that a skipped review, a lowered tier, or a commit pushed after the
review shows on the PR instead of passing quietly.
"""

import json
import os
import re
import subprocess
import sys

TIERS = ["readback", "readback+correctness", "full"]
QUIET_DEFAULT = [r"\.md$", r"^docs/", r"^\.agents/", r"^\.claude/", r"^\.codex/", r"^\.vscode/",
                 r"^\.github/labels\.json$", r"^NOTICE$", r"^LICENSE$"]
SMALL_LINES = 30  # changed lines outside the quiet paths, tests included
HEAVY = {"sol", "opus"}  # the models that may run the correctness axis
MODELS = {"sol", "opus", "terra", "luna", "sonnet"}
LINE = "- <axis> (<model>): <outcome>"
FAMILY = {"sol": "codex", "terra": "codex", "luna": "codex", "opus": "claude", "sonnet": "claude"}
FLAGS = {"tier": set(), "check": {"--pr", "--body", "--base"}}
MODELS_MD = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "..", "agents", "models.md")
INSTALLED = "~/.agents/workflow"
BRIEFS = {"readback": "skills/code-review/READBACK.md", "correctness": "skills/code-review/CORRECTNESS.md",
          "standards": "skills/code-review/SKILL.md", "spec": "skills/code-review/SKILL.md"}
AUTHORS = {"claude": "Claude", "codex": "Codex"}
USAGE = "usage: review.py tier [base] | check [--pr <n> | --body <file> [--base <ref>]]"


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()


def lines(text):
    return [line for line in text.splitlines() if line]


def load_rules(root):
    path = os.path.join(root, "docs", "agents", "review.md")
    rules = {"full": [], "quiet": [re.compile(p) for p in QUIET_DEFAULT]}
    if not os.path.exists(path):
        return rules
    block = re.search(r"^```review-paths\n(.*?)^```", open(path, encoding="utf-8").read(), re.M | re.S)
    if not block:
        return rules
    for raw in block.group(1).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "both-families":
            continue
        elif m := re.match(r"^full\s+([^:]+):\s*(.+)$", line):
            rules["full"].append((m.group(1).strip(), re.compile(m.group(2).strip(), re.I)))
        elif m := re.match(r"^quiet:\s*(.+)$", line):
            rules["quiet"].append(re.compile(m.group(1).strip()))
        else:
            sys.exit(f"review.md review-paths: cannot read line: {line}")
    return rules


def quiet(path, rules):
    return any(p.search(path) for p in rules["quiet"])


def tier_of(paths, rules):
    reasons = [f"{area}: {p}" for p in paths for area, rx in rules["full"] if rx.search(p)]
    if reasons:
        return "full", reasons
    if paths and all(quiet(p, rules) for p in paths):
        return "readback", []
    return "readback+correctness", []


def small(tier, counts, rules):
    """counts: {path: changed lines, or None for a binary file}. The loud line count of a small diff, else None."""
    loud = [n for path, n in counts.items() if not quiet(path, rules)]
    if tier != "readback+correctness" or None in loud or sum(loud) > SMALL_LINES:
        return None
    return sum(loud)


def requirements(tier, rules):
    """Each requirement is (axis, allowed models or None)."""
    if tier == "full":
        return [("standards", None), ("spec", None), ("correctness", {"sol"}), ("correctness", {"opus"})]
    if tier == "readback+correctness":
        return [("readback", None), ("correctness", HEAVY)]
    return [("readback", None)]


def load_models(text):
    """agents/models.md read into its table rows ({role: (model cell, effort)}) and model ids ({name: id})."""
    rows = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 4 and not set(cells[0]) <= set("- "):
            for role in cells[0].split(","):
                rows[role.strip().lower()] = (cells[2], cells[3])
    blocks = re.findall(r"^```model-ids[ \t]*\n(.*?)^```[ \t]*$", text, re.M | re.S)
    if len(blocks) != 1:
        sys.exit(f"agents/models.md needs one ```model-ids block, and has {len(blocks)}")
    ids = {}
    for raw in blocks[0].splitlines():
        if not raw.strip():
            continue
        if not (m := re.match(r"^\s*(\w+):\s*([\w.-]+/[\w.-]+)\s*$", raw)):
            sys.exit(f"agents/models.md model-ids: cannot read line: {raw.strip()}")
        if m.group(1).lower() in ids:
            sys.exit(f"agents/models.md model-ids: {m.group(1)} has two lines")
        ids[m.group(1).lower()] = m.group(2)
    return {"rows": rows, "ids": ids}


def reviewers(needs, author, models):
    """(axis, model id, effort, brief) for each of the needed reviewers, when `author`'s family wrote the change."""
    out = []
    for axis, allowed in needs:
        if axis not in models["rows"]:
            sys.exit(f"agents/models.md has no {axis.capitalize()} row")
        cell, effort = models["rows"][axis]
        if not effort:
            sys.exit(f"agents/models.md: the {axis.capitalize()} row has no effort")
        if allowed and len(allowed) == 1:
            name = next(iter(allowed))
        elif m := re.search(r"(\w+), or (\w+) when Codex wrote it", cell):
            name = (m.group(2) if author == "codex" else m.group(1)).lower()
        else:
            sys.exit(f"agents/models.md: cannot read the {axis.capitalize()} row's model: {cell}")
        if allowed and name not in allowed:
            sys.exit(f"agents/models.md gives {axis} to {name.capitalize()}, which the review record does not accept "
                     f"for it: {' or '.join(sorted(m.capitalize() for m in allowed))}")
        if name not in models["ids"]:
            sys.exit(f"agents/models.md names no id for {name.capitalize()} in its ```model-ids block")
        out.append((axis, models["ids"][name], effort, BRIEFS[axis]))
    return out


def label(req):
    axis, models = req
    return f"{axis} ({' or '.join(sorted(m.capitalize() for m in models))})" if models else axis


def parse_record(body):
    body = body.replace("\r\n", "\n")
    section = re.search(r"^## Review[ \t]*\n(.*?)(?=^## |\Z)", body, re.M | re.S)
    if not section:
        return None
    head = re.search(r"^Tier:\s*`?(full|readback\+correctness|readback)`?\s*,\s*reviewed\s+`?([0-9a-f]{7,40})`?",
                     section.group(1), re.M | re.I)
    if not head:
        return None
    axes, unread = [], []
    for line in re.findall(r"^[-*]\s+(?:readback|standards|spec|correctness)\s*\(.*$", section.group(1), re.M | re.I):
        if m := re.match(r"^[-*]\s+(readback|standards|spec|correctness)\s*\((\w+)\)\s*:\s*(.*)$", line, re.I):
            axes.append((m.group(1).lower(), m.group(2).lower(), bool(re.match(r"skipped\b", m.group(3).strip(), re.I))))
        elif not re.match(r"^[-*]\s+\w+\s*\(\w+\)", line):
            # Only a model name the parser cannot read: an annotated extra line
            # (`- correctness (Sol), fix round: ...`) stays a note, as it always was.
            unread.append(line)
    return {"tier": head.group(1).lower(), "reviewed": head.group(2), "axes": axes, "unread": unread}


def check_record(record, changed, later, rules):
    """later: [(sha, [paths])] of the branch's own commits after the reviewed one, or None."""
    derived, reasons = tier_of(changed, rules)
    if record is None:
        need = ", ".join(label(r) for r in requirements(derived, rules))
        return [f"The PR body has no review record. Add `## Review` with `Tier: {derived}, reviewed <sha>` "
                f"and a line per reviewer: {need} (the `pr` skill)."], []
    violations, warnings = [], []
    tier = record["tier"]
    if TIERS.index(tier) < TIERS.index(derived):
        loud = ", ".join(p for p in changed if not quiet(p, rules))
        violations.append(f"The record says tier {tier}, but the diff is {derived}: "
                          f"{'; '.join(reasons) or 'these paths change behaviour: ' + loud}. It needs "
                          f"{', '.join(label(r) for r in requirements(derived, rules))}.")
        tier = derived
    for line in record.get("unread", []):
        violations.append(f"Cannot read the reviewer line `{line}`. Write `{LINE}`, the model one word of "
                          f"{', '.join(sorted(MODELS))}.")
    for axis, model, _ in record["axes"]:
        if model not in MODELS:
            violations.append(f"Unknown model `{model}` on the {axis} line; use one of {', '.join(sorted(MODELS))}.")
    for req in requirements(tier, rules):
        axis, models = req
        hits = [a for a in record["axes"] if a[0] == axis and (models is None or a[1] in models)]
        if not hits:
            violations.append(f"Tier {tier} needs a {label(req)} line in the record, as `{LINE}`.")
        elif all(a[2] for a in hits):
            warnings.append(f"{label(req)} is recorded as skipped.")
    if later is None:
        violations.append(f"The reviewed commit {record['reviewed']} is not on this branch. After a rebase, "
                          "record the commit that now holds what was reviewed.")
    else:
        for sha, paths in later:
            loud = [p for p in paths if not quiet(p, rules)]
            if loud:
                violations.append(f"Commit {sha} changes {', '.join(loud)} after the reviewed commit "
                                  f"{record['reviewed']}. Run the fix round on `git diff {record['reviewed']}..HEAD` "
                                  "and record the new head.")
    return violations, warnings


def commits_after(reviewed, base, head):
    try:
        git("merge-base", "--is-ancestor", reviewed, head)
    except subprocess.CalledProcessError:
        return None
    return [(sha[:7], lines(git("diff-tree", "--no-commit-id", "--name-only", "-r", sha)))
            for sha in lines(git("rev-list", "--no-merges", f"{reviewed}..{head}", f"^{base}"))]


def default_base():
    try:
        return git("symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    except subprocess.CalledProcessError:
        return "main"


def line_counts(base):
    """{path: changed lines} of the working tree against its merge-base with base; None for a binary file."""
    counts = {}
    for row in lines(git("diff", "--numstat", "--no-renames", git("merge-base", base, "HEAD"))):
        added, deleted, path = row.split("\t", 2)
        counts[path] = None if added == "-" else int(added) + int(deleted)
    for path in lines(git("ls-files", "--others", "--exclude-standard")):
        try:
            text = open(path, encoding="utf-8").read()
            counts[path] = None if "\0" in text else len(text.splitlines())
        except (UnicodeDecodeError, OSError):
            counts[path] = None
    return counts


def print_tier(base, rules):
    paths = sorted(set(lines(git("diff", "--name-only", f"{base}...HEAD")))
                   | set(lines(git("diff", "--name-only", "HEAD")))
                   | set(lines(git("ls-files", "--others", "--exclude-standard"))))
    tier, reasons = tier_of(paths, rules)
    print(f"Tier: {tier}")
    for r in reasons:
        print(f"  {r}")
    needs = requirements(tier, rules)
    n = small(tier, line_counts(base), rules)
    if n is not None:
        print(f"Small: {n} changed line{'' if n == 1 else 's'} outside the quiet paths (limit {SMALL_LINES})")
        needs = [r for r in needs if r[0] != "readback"]
    with open(MODELS_MD, encoding="utf-8") as f:
        models = load_models(f.read())
    print(f"Each reviewer's task opens with {INSTALLED}/agents/reviewer.md, then its brief.")
    for author, name in AUTHORS.items():
        print(f"When {name} wrote it:")
        for axis, model_id, effort, brief in reviewers(needs, author, models):
            print(f"  {axis}: {model_id}, reasoning {effort}, brief {INSTALLED}/{brief}")
    print("Reviewers: " + ", ".join(label(r) for r in needs))


def run_check(args, rules):
    if "--pr" in args:
        n = args[args.index("--pr") + 1]
        pr = json.loads(subprocess.run(["gh", "pr", "view", n, "--json", "body,baseRefName,headRefOid,author"],
                                       check=True, capture_output=True, text=True).stdout)
        # The head too: a push or `gh pr update-branch` may not have reached this checkout yet.
        git("fetch", "-q", "origin", pr["baseRefName"], f"pull/{n}/head")
        body, head, author = pr["body"], pr["headRefOid"], pr["author"]["login"]
        base = git("merge-base", f"origin/{pr['baseRefName']}", head)
    elif "--body" in args:
        # Before a push: the head is the checkout's, and only a Dependabot author skips the check.
        body = open(args[args.index("--body") + 1], encoding="utf-8").read()
        head, author = git("rev-parse", "HEAD"), ""
        base = args[args.index("--base") + 1] if "--base" in args else git("merge-base", default_base(), head)
    else:
        body, base, head = os.environ.get("PR_BODY"), os.environ.get("BASE_SHA"), os.environ.get("HEAD_SHA")
        author = os.environ.get("PR_AUTHOR", "")
        if None in (body, base, head):
            sys.exit("set PR_BODY, BASE_SHA and HEAD_SHA, or pass --pr <n> or --body <file>")
    if author in ("dependabot[bot]", "app/dependabot"):
        print("Dependabot PR: no review record expected.")
        return 0
    record = parse_record(body)
    changed = lines(git("diff", "--name-only", f"{base}...{head}"))
    later = commits_after(record["reviewed"], base, head) if record else []
    violations, warnings = check_record(record, changed, later, rules)
    gha = os.environ.get("GITHUB_ACTIONS") == "true"
    for w in warnings:
        print(("::warning::" if gha else "warning: ") + w)
    for v in violations:
        print(("::error::" if gha else "error: ") + v, file=sys.stderr)
    if not violations:
        print("review record: ok")
    return 1 if violations else 0


def main(argv):
    if not argv or argv[0] not in ("tier", "check"):
        sys.exit(__doc__)
    unknown = [a for a in argv[1:] if a.startswith("-") and a not in FLAGS[argv[0]]]
    if unknown:
        print(f"{USAGE} (unknown option {unknown[0]})", file=sys.stderr)
        return 2
    rules = load_rules(git("rev-parse", "--show-toplevel"))
    if argv[0] == "tier":
        print_tier(argv[1] if len(argv) > 1 else default_base(), rules)
        return 0
    return run_check(argv[1:], rules)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
