"""Unit tests for lib/parts.py: every part fits one Read, nothing is lost, and the index lists it all."""

import importlib.util
import os
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
spec = importlib.util.spec_from_file_location("parts", os.path.join(ROOT, "lib/parts.py"))
parts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parts)


def slurp(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def diff(path, hunks, lines_per_hunk, width=60):
    head = f"--- a/{path}\n+++ b/{path}\n"
    body = "".join(f"@@ -{h},1 +{h},1 @@\n" + "".join(f"+{'x' * width} {h}.{i}\n" for i in range(lines_per_hunk))
                   for h in range(hunks))
    return head + body


class Split(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()
        self.p = parts.Parts(self.out)

    def read(self, name):
        return slurp(os.path.join(self.out, name))

    def assert_all_fit(self, names):
        for n in names:
            self.assertTrue(parts.fits(self.read(n)), n)

    def test_small_files_share_one_part(self):
        a, b = diff("a.ts", 1, 3), diff("b.ts", 1, 3)
        names = self.p.add("watched", "diff", [("a.ts", a), ("b.ts", b)])
        self.assertEqual(names, ["watched.1.diff"])
        self.assertEqual(self.read(names[0]), a + b)

    def test_files_are_not_split_when_they_fit_alone(self):
        sections = [(f"f{i}.ts", diff(f"f{i}.ts", 4, 60)) for i in range(8)]
        names = self.p.add("watched", "diff", sections)
        self.assertGreater(len(names), 1)
        self.assert_all_fit(names)
        self.assertEqual("".join(self.read(n) for n in names), "".join(t for _, t in sections))
        for n in names:
            self.assertTrue(self.read(n).startswith("--- a/f"), n)

    def test_a_big_file_is_cut_at_hunks_with_its_header_repeated(self):
        big = diff("big.ts", 40, 30)
        names = self.p.add("watched", "diff", [("big.ts", big)])
        self.assertGreater(len(names), 1)
        self.assert_all_fit(names)
        for n in names:
            text = self.read(n)
            self.assertTrue(text.startswith("--- a/big.ts\n+++ b/big.ts\n@@ "), n)
        body = "".join(self.read(n).split("+++ b/big.ts\n", 1)[1] for n in names)
        self.assertEqual(body, big.split("+++ b/big.ts\n", 1)[1])

    def test_a_single_huge_hunk_is_cut_between_lines(self):
        added = diff("new.ts", 1, 3000)
        names = self.p.add("watched", "diff", [("new.ts", added)])
        self.assertGreater(len(names), 1)
        self.assert_all_fit(names)
        body = "".join(self.read(n).split("+++ b/new.ts\n", 1)[1] for n in names)
        self.assertEqual(body, added.split("+++ b/new.ts\n", 1)[1])

    def test_a_list_is_cut_between_lines(self):
        items = [("", f"- #{i} {'item ' * 30}\n") for i in range(2000)]
        names = self.p.add("release-items", "md", items)
        self.assertGreater(len(names), 1)
        self.assert_all_fit(names)
        self.assertEqual("".join(self.read(n) for n in names), "".join(t for _, t in items))

    def test_nothing_written_for_empty_sections(self):
        self.assertEqual(self.p.add("watched", "diff", [("a.ts", "")]), [])
        self.assertEqual(os.listdir(self.out), [])

    def test_index_lists_every_part_with_its_paths(self):
        self.p.add("release-items", "md", [("", "- #1 x\n")])
        big = diff("big.ts", 40, 30)
        names = self.p.add("watched", "diff", [("big.ts", big), ("small.ts", diff("small.ts", 1, 2))])
        index = slurp(self.p.write_index())
        self.assertIn("`release-items.1.md`", index)
        for n in names:
            self.assertIn(f"`{n}`", index)
        self.assertIn(f"`big.ts (piece 1 of {len(names)})`", index)
        self.assertIn("`small.ts`", index)
        self.assertTrue(parts.fits(index))

    def test_index_says_when_there_is_nothing(self):
        self.assertIn("Nothing to read", slurp(self.p.write_index()))

    def test_a_line_too_long_for_one_part_is_cut_into_lines(self):
        line = "+" + "y" * 100_000 + "\n"
        names = self.p.add("watched", "diff", [("min.js", "--- a/min.js\n+++ b/min.js\n@@ -0,0 +1 @@\n" + line)])
        self.assertGreater(len(names), 1)
        self.assert_all_fit(names)
        body = "".join(self.read(n).split("+++ b/min.js\n", 1)[1] for n in names)
        self.assertEqual(body.replace("\n", ""), "@@ -0,0 +1 @@" + line.replace("\n", ""))
        self.assertTrue(all(len(l) <= parts.MAX_LINE for l in body.splitlines()))

    def test_a_line_that_fits_only_without_its_header_is_cut_too(self):
        line = "+" + "x" * (parts.MAX_CHARS - parts.PREFIX - 2) + "\n"
        self.assertTrue(parts.fits(line))
        names = self.p.add("watched", "diff", [("x", "--- a/x\n+++ b/x\n@@ -0,0 +1 @@\n" + line)])
        self.assert_all_fit(names)

    def test_an_index_too_big_for_one_read_is_cut_into_parts(self):
        sections = [("p/" + "d" * 170 + f"/{i}.md", diff(f"{i}.md", 1, 1)) for i in range(400)]
        self.p.add("src", "diff", sections)
        index = slurp(self.p.write_index())
        self.assertTrue(parts.fits(index))
        pages = sorted(n for n in os.listdir(self.out) if n.startswith("index.") and n != "index.md")
        self.assertGreater(len(pages), 1)
        for n in pages:
            self.assertIn(f"`{n}`", index)
            self.assertTrue(parts.fits(self.read(n)), n)
        listed = "".join(self.read(n) for n in pages)
        for path, _ in sections:
            self.assertIn(f"`{path}`", listed)

    def test_non_ascii_round_trips(self):
        text = "--- a/x\n+++ b/x\n@@ -1 +1 @@\n+José ñ 日本\n"
        names = self.p.add("src", "diff", [("x", text)])
        self.assertEqual(self.read(names[0]), text)


if __name__ == "__main__":
    unittest.main()
