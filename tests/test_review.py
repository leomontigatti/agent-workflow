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


MODELS_MD = """# Roles and models

| Role            | What it does | Model                                                    | Effort | Fallback |
| --------------- | ------------ | -------------------------------------------------------- | ------ | -------- |
| Standards, Spec | two axes     | the other family: Sol, or Opus when Codex wrote it       | medium | recorded |
| Correctness     | the bug hunt | full tier: both, Opus and Sol; else the other family: Sol, or Opus when Codex wrote it | high | recorded |
| Readback        | restates     | Terra, or Sonnet when Codex wrote it                     | low    | recorded |

## Reaching each model

A model id is the provider, a slash, then the model: `acme` for Sol (`sol-9`) and
Terra (`terra-9`); `beta` for Opus (`opus-9`) and Sonnet (`sonnet-9`).
"""


class Reviewers(unittest.TestCase):
    """What the orchestrator starts for a tier: each reviewer's model id, effort and brief."""

    def test_the_readback_model_follows_the_author(self):
        models = review.load_models(MODELS_MD)
        self.assertEqual(review.reviewers("readback", "claude", models),
                         [("readback", "acme/terra-9", "low", "skills/code-review/READBACK.md")])
        self.assertEqual(review.reviewers("readback", "codex", models),
                         [("readback", "beta/sonnet-9", "low", "skills/code-review/READBACK.md")])

    def test_correctness_runs_on_the_other_family_at_its_rows_effort(self):
        models = review.load_models(MODELS_MD)
        self.assertEqual(review.reviewers("readback+correctness", "claude", models)[1],
                         ("correctness", "acme/sol-9", "high", "skills/code-review/CORRECTNESS.md"))
        self.assertEqual(review.reviewers("readback+correctness", "codex", models)[1],
                         ("correctness", "beta/opus-9", "high", "skills/code-review/CORRECTNESS.md"))

    def test_the_full_tier_runs_correctness_on_both_families_whoever_wrote_it(self):
        models = review.load_models(MODELS_MD)
        for author in ("claude", "codex"):
            got = review.reviewers("full", author, models)
            self.assertEqual([r[0] for r in got], ["standards", "spec", "correctness", "correctness"])
            self.assertEqual(sorted(r[1] for r in got[2:]), ["acme/sol-9", "beta/opus-9"])
        self.assertEqual(review.reviewers("full", "claude", models)[0],
                         ("standards", "acme/sol-9", "medium", "skills/code-review/SKILL.md"))

    def test_each_id_takes_the_provider_named_before_it_whatever_ends_the_clause(self):
        models = review.load_models(MODELS_MD.replace("(`terra-9`); `beta` for", "(`terra-9`). `beta`\nfor"))
        self.assertEqual(review.reviewers("readback", "codex", models)[0][1], "beta/sonnet-9")

    def test_a_model_with_no_id_fails_naming_it(self):
        broken = MODELS_MD.replace("Terra (`terra-9`)", "Luna (`luna-9`)")
        with self.assertRaises(SystemExit) as cm:
            review.reviewers("readback", "claude", review.load_models(broken))
        self.assertIn("Terra", str(cm.exception))

    def test_the_real_table_gives_every_reviewer_a_model_and_a_brief(self):
        with open(os.path.join(ROOT, "agents", "models.md"), encoding="utf-8") as f:
            models = review.load_models(f.read())
        for tier in review.TIERS:
            for author in ("claude", "codex"):
                for axis, model_id, effort, brief in review.reviewers(tier, author, models):
                    self.assertRegex(model_id, r"^[a-z]+/[\w.-]+$", (tier, author, axis))
                    self.assertIn(effort, {"low", "medium", "high"}, (tier, author, axis))
                    self.assertTrue(os.path.isfile(os.path.join(ROOT, brief)), brief)


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

    def test_a_terra_readback_passes(self):
        v, _ = self.check(body("readback", "- readback (Terra): ok"), ["docs/a.md"])
        self.assertEqual(v, [])

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

    def test_an_annotated_extra_line_still_passes(self):
        # Shapes rubens PRs use for fix rounds (#319, #348, #365), beside a plain line.
        v, _ = self.check(body("readback+correctness", "- readback (luna): ok",
                               "- readback (Luna), over abcd51a (the tools report): no findings",
                               "- correctness (sol): ok", "- correctness fix round (Sol): no findings",
                               "- correctness (Sol), fix round: no findings"), ["app/x.ts"])
        self.assertEqual(v, [])

    def test_a_model_id_in_the_parentheses_fails(self):
        # rubens#332's first body.
        v, _ = self.check(body("readback", "- readback (gpt-6-luna): ok"), ["docs/a.md"])
        self.assertTrue(any("(gpt-6-luna)" in x and review.LINE in x for x in v))

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


class Checkout(unittest.TestCase):
    """A clone of a one-commit origin, on branch `feat`, where the script runs from its command line."""

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

    def run_script(self, *args):
        return subprocess.run([sys.executable, "-I", os.path.join(ROOT, "skills/implement/scripts/review.py"), *args],
                              cwd=self.work, capture_output=True, text=True, env=self.env)


class TierCommand(Checkout):
    """`tier [base]`: the tier of the branch, from the command line."""

    def test_a_flag_as_the_base_is_refused_with_a_usage_line(self):
        run = self.run_script("tier", "--base", "origin/main")
        self.assertEqual(run.returncode, 2)
        self.assertNotIn("Traceback", run.stderr)
        self.assertEqual(len(run.stderr.strip().splitlines()), 1, run.stderr)
        self.assertTrue(run.stderr.startswith("usage: "), run.stderr)

    def test_a_plain_base_and_no_base_both_read_the_branch(self):
        self.commit("src/app.py")
        for args in (("tier", "origin/main"), ("tier",)):
            run = self.run_script(*args)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("Tier: readback+correctness", run.stdout)

    def test_the_tier_line_comes_first_and_each_reviewer_follows_with_its_effort_and_brief(self):
        self.commit("src/app.py")
        run = self.run_script("tier")
        self.assertEqual(run.returncode, 0, run.stderr)
        out = run.stdout.splitlines()
        self.assertEqual(out[0], "Tier: readback+correctness")
        self.assertTrue(any(line.lstrip().startswith("readback: ") and "reasoning low" in line
                            and "~/.agents/workflow/skills/code-review/READBACK.md" in line for line in out), out)
        self.assertTrue(any(line.lstrip().startswith("correctness: ") and "reasoning medium" in line
                            and "~/.agents/workflow/skills/code-review/CORRECTNESS.md" in line for line in out), out)
        self.assertIn("When Claude wrote it:", out)
        self.assertIn("When Codex wrote it:", out)


class CheckBody(Checkout):
    """`check --body <file>`: the record checked from the checkout, before the push."""

    def run_check(self, text, *extra):
        path = os.path.join(self.tmp, "body.md")
        with open(path, "w") as f:
            f.write(text)
        return self.run_script("check", "--body", path, *extra)

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

    def test_a_flag_as_the_base_is_refused_with_a_usage_line(self):
        sha = self.commit("a.md")
        run = self.run_check(body("readback", "- readback (luna): ok").replace("abc1234", sha), "--base", "--cached")
        self.assertEqual(run.returncode, 2)
        self.assertNotIn("Traceback", run.stderr)
        self.assertEqual(len(run.stderr.strip().splitlines()), 1, run.stderr)
        self.assertTrue(run.stderr.startswith("usage: "), run.stderr)


if __name__ == "__main__":
    unittest.main()
