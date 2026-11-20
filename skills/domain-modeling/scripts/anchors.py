#!/usr/bin/env python3
"""List the ADRs and glossary terms whose anchor has left the code.

Usage, from a project checkout: python3 -I anchors.py

- An ADR, a file under `docs/adr/` whose name starts with its number, names what it governs on a
  `Governs:` line, each anchor in backticks. One written like a path (a slash, a `*`, a file
  extension) must match a file in the tree, as a glob or a directory; any other is an identifier
  some file outside `docs/adr/` and `GLOSSARY.md` must contain as a whole word.
- A `GLOSSARY.md` term (written `sale_order` in bold) must appear as a whole name in a file that is
  not Markdown, under any casing, with `_`, `-` or nothing between its words, and with or without
  a final `s` or `es` (`SaleOrder`, `sale-orders`). A longer name that contains it
  (`sale_order_id`, `keeps-sale-orders`) does not count, and neither do its words spelled apart
  (`sale order`): the entry is the name the code uses. The match reads text, so a name left in a
  comment still counts. A retired term is skipped, and a glossary with no other entry is reported
  as `no terms:`.

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
    return git("grep", "--untracked", "-I", "-lz", flag, "-e", pattern, "--", ".", *excluded).stdout.split("\0")[:-1]


def whole_word(pattern, paths, flags=0, joiner=""):
    """joiner: characters that, like a letter, make the match part of a longer name."""
    word = re.compile(rf"(?<![\w{joiner}])(?:{pattern})(?![\w{joiner}])", flags)
    return any(word.search(open(p, encoding="utf-8", errors="replace").read()) for p in paths)


def adr_gone(token, files):
    if "/" in token or "*" in token or re.search(r"\.\w+$", token):
        folder = token.rstrip("/") + "/"
        return not any(fnmatch.fnmatch(f, token) or f.startswith(folder) for f in files)
    return not whole_word(re.escape(token), in_code("-F", token, ":!docs/adr", ":!GLOSSARY.md"))


def term_gone(term):
    parts = [re.escape(p) for p in re.split(r"[_\s-]+|(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", term) if p]
    name = "[_-]?".join(parts)
    return bool(parts) and not whole_word(name + "(?:s|es)?", in_code("-iE", name, ":!*.md"), re.I, "-")


def main():
    os.chdir(git("rev-parse", "--show-toplevel").stdout.strip() or ".")
    files = [f for f in git("ls-files", "-z", "--cached", "--others", "--exclude-standard").stdout.split("\0")
             if os.path.isfile(f)]
    gone = 0
    for path in sorted(glob.glob("docs/adr/[0-9]*.md")):
        governs = re.search(r"^Governs:(.*)$", open(path, encoding="utf-8").read(), re.M)
        if not governs:
            print(f"no anchor: {path}")
            continue
        for token in re.findall(r"`([^`]+)`", governs.group(1)):
            if adr_gone(token, files):
                print(f"gone: {path} governs `{token}`")
                gone += 1
    if os.path.exists("GLOSSARY.md"):
        terms = [m.group(1) for line in open("GLOSSARY.md", encoding="utf-8")
                 if (m := re.match(r"\*\*`([^`]+)`\*\*", line)) and "retired term" not in line]
        if not terms:
            print("no terms: GLOSSARY.md has no current entry written as a code identifier in bold backticks, so none is checked")
        for term in terms:
            if term_gone(term):
                print(f"gone: GLOSSARY.md term `{term}`")
                gone += 1
    if gone:
        return 1
    print("anchors: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
