#!/usr/bin/env python3
"""List the ADRs and glossary terms whose anchor has left the code.

Usage, from a project checkout: python3 -I anchors.py

- An ADR under `docs/adr/` names what it governs on a `Governs:` line, each anchor in backticks.
  One written like a path (a slash, a `*`, a file extension) must match a file in the tree, as a
  glob or a directory; any other is an identifier some file outside `docs/adr/` and `GLOSSARY.md`
  must contain.
- A `GLOSSARY.md` term (written `sale_order` in bold) must appear in a file that is not Markdown, under any
  casing or separator (`SaleOrder`, `sale-order`). A retired term is skipped.

Prints one `gone:` line per missing anchor and exits 1 when there is one: the decision or the term
may be stale. An ADR with no `Governs:` line is listed as `no anchor:` and passes. Files not yet
committed count as the tree; ignored ones do not.
"""

import fnmatch
import glob
import os
import re
import subprocess
import sys


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def in_code(flag, pattern, *excluded):
    return git("grep", "--untracked", "-I", "-q", flag, "-e", pattern, "--", ".", *excluded).returncode == 0


def adr_gone(token, files):
    if "/" in token or "*" in token or re.search(r"\.\w+$", token):
        folder = token.rstrip("/") + "/"
        return not any(fnmatch.fnmatch(f, token) or f.startswith(folder) for f in files)
    return not in_code("-F", token, ":!docs/adr", ":!GLOSSARY.md")


def term_gone(term):
    parts = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])", term)
    return bool(parts) and not in_code("-iE", "[_ -]?".join(parts), ":!*.md")


def main():
    os.chdir(git("rev-parse", "--show-toplevel").stdout.strip() or ".")
    files = git("ls-files", "--cached", "--others", "--exclude-standard").stdout.splitlines()
    gone = 0
    for path in sorted(glob.glob("docs/adr/*.md")):
        governs = re.search(r"^Governs:(.*)$", open(path, encoding="utf-8").read(), re.M)
        if not governs:
            print(f"no anchor: {path}")
            continue
        for token in re.findall(r"`([^`]+)`", governs.group(1)):
            if adr_gone(token, files):
                print(f"gone: {path} governs `{token}`")
                gone += 1
    if os.path.exists("GLOSSARY.md"):
        for line in open("GLOSSARY.md", encoding="utf-8"):
            term = re.match(r"\*\*`([^`]+)`\*\*", line)
            if term and "retired term" not in line and term_gone(term.group(1)):
                print(f"gone: GLOSSARY.md term `{term.group(1)}`")
                gone += 1
    if gone:
        return 1
    print("anchors: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
