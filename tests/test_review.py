"""Unit tests for skills/implement/scripts/review.py: tiers and the record check."""

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
spec = importlib.util.spec_from_file_location("review", os.path.join(ROOT, "skills/implement/scripts/review.py"))
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


def rules(both=False):
    r = {"full": [("money", re.compile(r"^app/finances/", re.I)), ("migration", re.compile(r"^db/migrations/"))],
         "quiet": [re.compile(p) for p in review.QUIET_DEFAULT], "both": both}
    return r


BODY = """## Summary

x

## Review

Tier: {tier}, reviewed abc1234

{lines}

Closes #1
"""


def body(tier, *axis_lines):
    return BODY.format(tier=tier, lines="\n".join(axis_lines))


class Tier(unittest.TestCase):
    def test_a_risky_path_is_full(self):
        self.assertEqual(review.tier_of(["app/finances/pay.ts", "README.md"], rules())[0], "full")

    def test_docs_only_keeps_the_readback(self):
        self.assertEqual(review.tier_of(["docs/x.md", ".claude/settings.json"], rules())[0], "readback")

    def test_code_outside_the_areas_adds_correctness(self):
        self.assertEqual(review.tier_of(["app/ui/button.ts"], rules())[0], "readback+correctness")


class Record(unittest.TestCase):
    def check(self, text, changed, later=(), both=False):
        return review.check_record(review.parse_record(text), changed, list(later), rules(both))

    def test_a_complete_full_record_passes(self):
        v, _ = self.check(body("full", "- standards (sol): no findings", "- spec (sol): no findings",
                               "- correctness (opus): 1 finding, fixed"), ["app/finances/a.ts"])
        self.assertEqual(v, [])

    def test_a_lowered_tier_fails(self):
        v, _ = self.check(body("readback", "- readback (luna): nothing surprising"), ["app/finances/a.ts"])
        self.assertTrue(any("but the diff is full" in x for x in v))

    def test_luna_cannot_run_correctness(self):
        v, _ = self.check(body("readback+correctness", "- readback (luna): ok", "- correctness (luna): ok"), ["app/x.ts"])
        self.assertTrue(any("correctness (Opus or Sol)" in x for x in v))

    def test_the_trial_needs_both_families(self):
        v, _ = self.check(body("full", "- standards (sol): ok", "- spec (sol): ok", "- correctness (sol): ok"),
                          ["app/finances/a.ts"], both=True)
        self.assertTrue(any("correctness (Opus)" in x for x in v))

    def test_a_skipped_axis_warns_but_passes(self):
        v, w = self.check(body("readback+correctness", "- readback (luna): ok",
                               "- correctness (opus): skipped, no route to Sol"), ["app/x.ts"])
        self.assertEqual(v, [])
        self.assertTrue(w)

    def test_a_code_commit_after_the_review_fails(self):
        v, _ = self.check(body("readback", "- readback (luna): ok"), ["docs/a.md"], later=[("def5678", ["app/x.ts"])])
        self.assertTrue(any("def5678" in x for x in v))

    def test_a_docs_commit_after_the_review_passes(self):
        v, _ = self.check(body("readback", "- readback (luna): ok"), ["docs/a.md"], later=[("def5678", ["docs/b.md"])])
        self.assertEqual(v, [])

    def test_a_rebased_away_review_fails(self):
        v, _ = review.check_record(review.parse_record(body("readback", "- readback (luna): ok")), ["docs/a.md"], None, rules())
        self.assertTrue(any("not on this branch" in x for x in v))

    def test_no_record_names_what_is_needed(self):
        v, _ = review.check_record(None, ["app/x.ts"], [], rules())
        self.assertIn("readback+correctness", v[0])


class CheckPr(unittest.TestCase):
    def test_a_pr_head_not_fetched_yet_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            # No user or system git config: a signing or hooks setting there would break the fixture.
            env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

            def git(cwd, *args):
                return subprocess.run(["git", "-C", cwd, *args], check=True, capture_output=True, text=True,
                                      env=env).stdout.strip()
            origin, work, local, bin_ = (os.path.join(tmp, d) for d in ("origin.git", "work", "local", "bin"))
            git(tmp, "init", "-q", "--bare", "-b", "main", origin)
            git(tmp, "clone", "-q", origin, work)
            for args in (("config", "user.email", "t@t"), ("config", "user.name", "t"),
                         ("commit", "-q", "--allow-empty", "-m", "base"), ("push", "-q", "origin", "main")):
                git(work, *args)
            git(tmp, "clone", "-q", origin, local)
            with open(os.path.join(work, "a.md"), "w") as f:
                f.write("x\n")
            git(work, "add", "a.md")
            git(work, "commit", "-q", "-m", "pr")
            head = git(work, "rev-parse", "HEAD")
            git(work, "push", "-q", "origin", "HEAD:refs/pull/1/head")
            pr = {"body": body("readback", "- readback (luna): ok").replace("abc1234", head[:7]),
                  "baseRefName": "main", "headRefOid": head, "author": {"login": "someone"}}
            os.mkdir(bin_)
            with open(os.path.join(bin_, "gh"), "w") as f:
                f.write("#!/bin/sh\ncat <<'JSON'\n" + json.dumps(pr) + "\nJSON\n")
            os.chmod(os.path.join(bin_, "gh"), 0o755)
            run = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "skills/implement/scripts/review.py"),
                                  "check", "--pr", "1"], cwd=local, capture_output=True, text=True,
                                 env={**env, "PATH": bin_ + os.pathsep + os.environ["PATH"]})
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("review record: ok", run.stdout)


if __name__ == "__main__":
    unittest.main()
