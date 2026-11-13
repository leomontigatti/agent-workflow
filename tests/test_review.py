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


def rules():
    return {"full": [("money", re.compile(r"^app/finances/", re.I)), ("migration", re.compile(r"^db/migrations/"))],
            "quiet": [re.compile(p) for p in review.QUIET_DEFAULT]}


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
    def check(self, text, changed, later=()):
        return review.check_record(review.parse_record(text), changed, list(later), rules())

    def test_a_complete_full_record_passes(self):
        v, _ = self.check(body("full", "- standards (sol): no findings", "- spec (sol): no findings",
                               "- correctness (opus): 1 finding, fixed", "- correctness (sol): no findings"),
                          ["app/finances/a.ts"])
        self.assertEqual(v, [])

    def test_a_lowered_tier_fails(self):
        v, _ = self.check(body("readback", "- readback (luna): nothing surprising"), ["app/finances/a.ts"])
        self.assertTrue(any("but the diff is full" in x for x in v))

    def test_luna_cannot_run_correctness(self):
        v, _ = self.check(body("readback+correctness", "- readback (luna): ok", "- correctness (luna): ok"), ["app/x.ts"])
        self.assertTrue(any("correctness (Opus or Sol)" in x for x in v))

    def test_the_full_tier_needs_both_families(self):
        v, _ = self.check(body("full", "- standards (sol): ok", "- spec (sol): ok", "- correctness (sol): ok"),
                          ["app/finances/a.ts"])
        self.assertTrue(any("correctness (Opus)" in x for x in v))

    def test_the_old_trial_line_still_reads(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "docs", "agents"))
            with open(os.path.join(root, "docs", "agents", "review.md"), "w") as f:
                f.write("```review-paths\nfull money: ^app/finances/\nboth-families\n```\n")
            self.assertEqual([area for area, _ in review.load_rules(root)["full"]], ["money"])

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


class CheckBody(unittest.TestCase):
    """`check --body <file>`: the record checked from the checkout, before the push."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = tmp.name
        # No user or system git config: a signing or hooks setting there would break the fixture.
        self.env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        origin, self.work = os.path.join(self.tmp, "origin.git"), os.path.join(self.tmp, "work")
        self.git(self.tmp, "init", "-q", "--bare", "-b", "main", origin)
        self.git(self.tmp, "clone", "-q", origin, self.work)
        for args in (("config", "user.email", "t@t"), ("config", "user.name", "t"),
                     ("commit", "-q", "--allow-empty", "-m", "base"), ("push", "-q", "origin", "main"),
                     ("remote", "set-head", "origin", "main"), ("checkout", "-q", "-b", "feat")):
            self.git(self.work, *args)

    def git(self, cwd, *args):
        return subprocess.run(["git", "-C", cwd, *args], check=True, capture_output=True, text=True,
                              env=self.env).stdout.strip()

    def commit(self, path):
        os.makedirs(os.path.dirname(os.path.join(self.work, path)) or self.work, exist_ok=True)
        with open(os.path.join(self.work, path), "a") as f:
            f.write("x\n")
        self.git(self.work, "add", path)
        self.git(self.work, "commit", "-q", "-m", path)
        return self.git(self.work, "rev-parse", "--short", "HEAD")

    def run_check(self, text, *extra):
        path = os.path.join(self.tmp, "body.md")
        with open(path, "w") as f:
            f.write(text)
        return subprocess.run([sys.executable, "-I", os.path.join(ROOT, "skills/implement/scripts/review.py"),
                               "check", "--body", path, *extra], cwd=self.work, capture_output=True, text=True,
                              env=self.env)

    def test_a_reviewed_branch_passes(self):
        sha = self.commit("a.md")
        run = self.run_check(body("readback", "- readback (luna): ok").replace("abc1234", sha))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("review record: ok", run.stdout)

    def test_a_full_model_name_fails_with_the_line_it_expects(self):
        # PR rubens#339's first body named each reviewer by its full model name.
        sha = self.commit("a.ts")
        run = self.run_check(body("readback+correctness", "- readback (GPT-6 Luna): ok",
                                  "- correctness (Claude Opus 5.5): no findings").replace("abc1234", sha))
        self.assertEqual(run.returncode, 1)
        self.assertIn("- correctness (Claude Opus 5.5)", run.stderr)
        self.assertIn("- <axis> (<model>): <outcome>", run.stderr)

    def test_a_raised_tier_names_the_path_that_raised_it(self):
        sha = self.commit("src/app.py")
        run = self.run_check(body("readback", "- readback (luna): ok").replace("abc1234", sha))
        self.assertEqual(run.returncode, 1)
        self.assertIn("src/app.py", run.stderr)
        self.assertIn("correctness (Opus or Sol)", run.stderr)

    def test_a_code_commit_after_the_review_needs_a_fix_round(self):
        sha = self.commit("a.ts")
        self.commit("b.ts")
        run = self.run_check(body("readback+correctness", "- readback (luna): ok", "- correctness (sol): ok")
                             .replace("abc1234", sha))
        self.assertEqual(run.returncode, 1)
        self.assertIn(f"git diff {sha}..HEAD", run.stderr)

    def test_the_base_can_be_given(self):
        self.commit("src/app.py")
        sha = self.commit("a.md")
        run = self.run_check(body("readback", "- readback (luna): ok").replace("abc1234", sha), "--base", "HEAD~1")
        self.assertEqual(run.returncode, 0, run.stderr)


if __name__ == "__main__":
    unittest.main()
