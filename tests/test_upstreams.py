"""Unit tests for skills/upstream-review/scripts/upstreams.py: `mark` moves only the watermarks."""

import importlib.util
import json
import os
import tempfile
import unittest
from datetime import date

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
spec = importlib.util.spec_from_file_location("upstreams", os.path.join(ROOT, "skills/upstream-review/scripts/upstreams.py"))
upstreams = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upstreams)

SOURCES = """{
  "sources": [
    {
      "id": "a",
      "repo": "o/a",
      "paths": ["a/**"],
      "reviewed": "1111111",
      "reviewedAt": "2026-01-01"
    },
    {
      "id": "b",
      "repo": "o/b",
      "paths": ["b/**", "c/**"],
      "reviewed": "2222222",
      "reviewedAt": "2026-01-01"
    }
  ]
}
"""


class Mark(unittest.TestCase):
    def run_mark(self, heads, report=True):
        d = tempfile.mkdtemp()
        upstreams.SOURCES = os.path.join(d, "sources.json")
        open(upstreams.SOURCES, "w").write(SOURCES)
        json.dump(heads, open(os.path.join(d, "heads.json"), "w"))
        rep = os.path.join(d, "report.md")
        if report:
            open(rep, "w").write("# report\n")
        upstreams.mark(d, rep)
        return open(upstreams.SOURCES).read()

    def test_moves_only_the_watermark_lines(self):
        out = self.run_mark({"a": "1111111", "b": "3333333"})
        today = date.today().isoformat()
        want = SOURCES.replace('"2222222",\n      "reviewedAt": "2026-01-01"',
                               f'"3333333",\n      "reviewedAt": "{today}"')
        self.assertEqual(out, want)

    def test_up_to_date_leaves_the_file_unchanged(self):
        self.assertEqual(self.run_mark({"a": "1111111", "b": "2222222"}), SOURCES)

    def test_refuses_without_a_report(self):
        with self.assertRaises(SystemExit):
            self.run_mark({"a": "9999999"}, report=False)


if __name__ == "__main__":
    unittest.main()
