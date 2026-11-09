"""Split a review script's output into parts that each fit one Read, and index them.

A collector (`changes.py`, `upstreams.py`) hands each output as a list of sections: one per file
for a diff, one per line for a list. `Parts.add` packs whole sections into parts under the limits
below, cuts a section that alone is too big at its `@@` hunk boundaries (repeating the file's
`---`/`+++` header in each piece), and cuts a hunk that is still too big between lines. A line
too long for one part is cut into shorter lines. `write_index` writes `index.md`, the list of every part with what it covers and its
size: the one file a review reads first.
"""

import os

# Read refuses a file over 25k tokens and shows 2,000 lines by default. Code and diffs run near
# three characters a token, and Read adds a line-number prefix to every line, so a part stays well
# under both.
MAX_CHARS = 40_000
MAX_LINES = 1_500
PREFIX = 8  # the characters Read's line-number prefix adds to each line
MAX_LINE = 2_000  # a line too long for one part (minified code, inlined data) is cut into lines this long


def size(text):
    lines = text.count("\n") + (0 if text.endswith("\n") or not text else 1)
    return len(text) + PREFIX * lines, lines


def fits(text):
    chars, lines = size(text)
    return chars <= MAX_CHARS and lines <= MAX_LINES


def _cut_lines(head, body):
    """Cut `body` between lines so each piece, with `head` before it, fits."""
    pieces, cur = [], ""
    for line in _short_lines(head, body):
        if cur and not fits(head + cur + line):
            pieces.append(head + cur)
            cur = ""
        cur += line
    if cur or not pieces:
        pieces.append(head + cur)
    return pieces


def _short_lines(head, text):
    """The lines of `text`, a line that cannot fit one part after `head` cut into shorter ones."""
    for line in text.splitlines(True):
        if fits(head + line):
            yield line
            continue
        bare = line.rstrip("\n")
        for i in range(0, len(bare), MAX_LINE):
            yield bare[i:i + MAX_LINE] + "\n"


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
        """Write `index.md`; when the list of parts is itself too big for one Read, cut it into
        `index.<n>.md` pages and make `index.md` the list of pages."""
        path = os.path.join(self.out, "index.md")
        lead = "Every file this run wrote for review, each sized to fit one Read. Read every one in full.\n\n"
        table = "| Part | Of | Size | Covers |\n|---|---|---|---|\n"
        rows = []  # one per file a part covers, so a page can end between any two
        for fname, of, covers, chars, lines in self.rows:
            for i, c in enumerate(covers or [None]):
                size = f"{chars:,} chars, {lines:,} lines" if i == 0 else ""
                rows.append(f"| `{fname}` | {of} | {size} | {f'`{c}`' if c else '(list)'} |\n")
        text = "# Parts\n\n" + lead + (table + "".join(rows) if rows else "Nothing to read: no source changed.\n")
        if not fits(text):
            title = "# Parts, page {} of {}\n\n"
            pages, cur = [], ""
            for row in rows:
                if cur and not fits(title.format(999, 999) + table + cur + row):
                    pages.append(table + cur)
                    cur = ""
                cur += row
            pages.append(table + cur)
            names = []
            for k, page in enumerate(pages, 1):
                names.append(f"index.{k}.md")
                with open(os.path.join(self.out, names[-1]), "w", encoding="utf-8") as f:
                    f.write(title.format(k, len(pages)) + page)
            text = ("# Parts\n\n" + lead.replace("Read every one in full.",
                    "The list is cut into the pages below: read each page, then every part it lists.")
                    + "".join(f"- `{n}`\n" for n in names))
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path
