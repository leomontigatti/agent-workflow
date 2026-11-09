"""Split a review script's output into parts that each fit one Read, and index them.

A collector (`changes.py`, `upstreams.py`) hands each output as a list of sections: one per file
for a diff, one per line for a list. `Parts.add` packs whole sections into parts under the limits
below, cuts a section that alone is too big at its `@@` hunk boundaries (repeating the file's
`---`/`+++` header in each piece), and cuts a hunk that is still too big between lines. `write_index`
writes `index.md`, the list of every part with what it covers and its size: the one file a review
reads first.
"""

import os

# Read refuses a file over 25k tokens and shows 2,000 lines by default. Code and diffs run near
# three characters a token, and Read adds a line-number prefix to every line, so a part stays well
# under both.
MAX_CHARS = 40_000
MAX_LINES = 1_500
PREFIX = 8  # the characters Read's line-number prefix adds to each line


def size(text):
    lines = text.count("\n") + (0 if text.endswith("\n") or not text else 1)
    return len(text) + PREFIX * lines, lines


def fits(text):
    chars, lines = size(text)
    return chars <= MAX_CHARS and lines <= MAX_LINES


def _cut_lines(head, body):
    """Cut `body` between lines so each piece, with `head` before it, fits."""
    pieces, cur = [], ""
    for line in body.splitlines(True):
        if cur and not fits(head + cur + line):
            pieces.append(head + cur)
            cur = ""
        cur += line
    if cur or not pieces:
        pieces.append(head + cur)
    return pieces


def _cut_section(text):
    """Cut one section at hunk boundaries, then between lines, keeping its file header on each."""
    lines = text.splitlines(True)
    first = next((i for i, l in enumerate(lines) if l.startswith("@@")), None)
    if first is None:
        return _cut_lines("", text)
    head = "".join(lines[:first])
    hunks, cur = [], []
    for line in lines[first:]:
        if line.startswith("@@") and cur:
            hunks.append("".join(cur))
            cur = []
        cur.append(line)
    hunks.append("".join(cur))
    pieces, body = [], ""
    for hunk in hunks:
        if body and not fits(head + body + hunk):
            pieces.append(head + body)
            body = ""
        if fits(head + hunk):
            body += hunk
        else:
            if body:
                pieces.append(head + body)
                body = ""
            pieces.extend(_cut_lines(head, hunk))
    if body:
        pieces.append(head + body)
    return pieces


class Parts:
    """The parts written into one output directory, in the order `add` was called."""

    def __init__(self, out):
        self.out = out
        self.rows = []  # (file name, output it belongs to, what it covers, chars, lines)

    def add(self, name, ext, sections):
        """Write `sections` ([(path or "", text)]) as `<name>.<n>.<ext>` parts; return the file names.

        A path names what a section is about (a diff's file) and goes in the index; a list's
        sections pass "" and the index shows the part's line count only. Nothing is written when
        every section is empty.
        """
        pieces = []  # (path, text, piece number, piece count)
        for path, text in sections:
            if not text:
                continue
            cut = [text] if fits(text) else _cut_section(text)
            pieces.extend((path, t, i + 1, len(cut)) for i, t in enumerate(cut))
        parts, cur, covers = [], "", []
        for path, text, i, n in pieces:
            if cur and not fits(cur + text):
                parts.append((cur, covers))
                cur, covers = "", []
            cur += text
            if path:
                covers.append(path if n == 1 else f"{path} (piece {i} of {n})")
        if cur:
            parts.append((cur, covers))
        names = []
        for k, (text, covers) in enumerate(parts, 1):
            fname = f"{name}.{k}.{ext}"
            with open(os.path.join(self.out, fname), "w", encoding="utf-8") as f:
                f.write(text)
            lines = size(text)[1]
            self.rows.append((fname, name, covers, len(text), lines))
            names.append(fname)
        return names

    def write_index(self):
        path = os.path.join(self.out, "index.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Parts\n\nEvery file this run wrote for review, each sized to fit one Read. "
                    "Read every one in full.\n\n")
            if not self.rows:
                f.write("Nothing to read: no source changed.\n")
                return path
            f.write("| Part | Of | Size | Covers |\n|---|---|---|---|\n")
            for fname, of, covers, chars, lines in self.rows:
                f.write(f"| `{fname}` | {of} | {chars:,} chars, {lines:,} lines | "
                        f"{'<br>'.join(f'`{c}`' for c in covers) or '(list)'} |\n")
        return path
