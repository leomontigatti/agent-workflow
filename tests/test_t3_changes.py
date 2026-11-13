"""Unit tests for skills/t3-update-review/scripts/changes.py: the digest of the dependency entries."""

import importlib.util
import os
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
spec = importlib.util.spec_from_file_location("changes", os.path.join(ROOT, "skills/t3-update-review/scripts/changes.py"))
changes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(changes)

SAMPLE = """# T3 Code dependencies: a project

Status of an entry:

- **active**: we rely on T3 behaving this way.

## Active

### worktree-per-thread

- **Relies on:** T3 runs the setup script.
- **Used by:** `skills/implement/THREADS.md`
- **Breaks if:** T3 stops applying `defaultThreadEnvMode` or running create-time scripts,
  starts the agent before an `async: false` script exits.

### own-worktrees-only

- **Breaks if:** cleanup removes worktrees outside its folder.

## Watching

### preview-login

- **Workaround:** log in by hand.
- **Would improve if:** the preview keeps a session across tabs.

## Ready

## Resolved

### old-thing

- **Adopted:** in #12.
"""


class Digest(unittest.TestCase):
    def test_every_entry_once_with_its_status_and_clause_on_one_line(self):
        path = os.path.join(tempfile.mkdtemp(), "t3-dependencies.md")
        with open(path, "w") as f:
            f.write(SAMPLE)
        lines = changes.digest([path]).splitlines()
        expected = {
            "worktree-per-thread": ("active", "Breaks if: T3 stops applying `defaultThreadEnvMode` or running "
                                              "create-time scripts, starts the agent"),
            "own-worktrees-only": ("active", "Breaks if: cleanup removes worktrees outside its folder."),
            "preview-login": ("watching", "Would improve if: the preview keeps a session across tabs."),
            "old-thing": ("resolved", None),
        }
        for entry, (status, clause) in expected.items():
            hits = [l for l in lines if f"`{entry}`" in l]
            self.assertEqual(len(hits), 1, entry)
            self.assertIn(f"({status})", hits[0])
            if clause:
                self.assertIn(clause, hits[0])
        self.assertIn(f"{path}:9 ", next(l for l in lines if "`worktree-per-thread`" in l))


if __name__ == "__main__":
    unittest.main()
