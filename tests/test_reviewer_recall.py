"""Unit tests for evals/reviewer-recall/run.py: per-model effort, old manifests, and the time and
cost each review records and the report prints."""

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
spec = importlib.util.spec_from_file_location("recall", os.path.join(ROOT, "evals/reviewer-recall/run.py"))
recall = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recall)

CLAUDE_OUT = {"type": "result", "is_error": False, "result": "## Findings\nnone", "total_cost_usd": 1.25,
              "duration_ms": 61000, "num_turns": 7,
              "usage": {"input_tokens": 10, "cache_creation_input_tokens": 2000, "cache_read_input_tokens": 30000,
                        "output_tokens": 900, "service_tier": "standard"}}
CODEX_OUT = "\n".join(json.dumps(e) for e in [
    {"type": "thread.started", "thread_id": "x"},
    {"type": "turn.started"},
    {"type": "item.completed", "item": {"type": "agent_message", "text": "done"}},
    {"type": "turn.completed", "usage": {"input_tokens": 15893, "cached_input_tokens": 7168, "output_tokens": 5,
                                         "reasoning_output_tokens": 3}},
]) + "\n"


class Models(unittest.TestCase):
    def test_each_model_names_its_own_effort(self):
        self.assertEqual(recall.parse_models("fable:low,opus:medium", "high"),
                         {"fable": {"model": "claude-fable-5-2", "effort": "low"},
                          "opus": {"model": "claude-opus-5-5", "effort": "medium"}})

    def test_a_bare_model_takes_the_run_effort(self):
        self.assertEqual(recall.parse_models("opus,sol", "high")["sol"], {"model": "gpt-6.1-sol", "effort": "high"})

    def test_unknown_model_or_effort_stops(self):
        for spec_ in ("gemini:low", "opus:extreme"):
            with self.assertRaises(SystemExit):
                recall.parse_models(spec_, "medium")

    def test_fable_is_a_claude_model(self):
        self.assertEqual(recall.FAMILY["fable"], "claude")


class Manifest(unittest.TestCase):
    def test_old_manifest_reads_as_one_effort_for_every_model(self):
        old = {"models": {"opus": "claude-opus-5-5", "sol": "gpt-6.1-sol"}, "effort": "high", "prompts": {}, "runs": ["a.opus.1"]}
        self.assertEqual(recall.normalize(old)["models"],
                         {"opus": {"model": "claude-opus-5-5", "effort": "high"},
                          "sol": {"model": "gpt-6.1-sol", "effort": "high"}})
        self.assertNotIn("effort", old)

    def test_old_manifest_without_effort_measured_medium(self):
        old = {"models": {"opus": "claude-opus-5-5"}, "prompts": {}, "runs": ["a.opus.1"]}
        self.assertEqual(recall.normalize(old)["models"]["opus"]["effort"], "medium")

    def test_a_directory_refuses_another_effort_for_a_model(self):
        out = tempfile.mkdtemp()
        recall.claim(out, {"opus": {"model": "claude-opus-5-5", "effort": "medium"}}, {"c": "h"}, ["c.opus.1"])
        with self.assertRaises(SystemExit):
            recall.claim(out, {"opus": {"model": "claude-opus-5-5", "effort": "low"}}, {"c": "h"}, ["c.opus.1"])
        recall.claim(out, {"fable": {"model": "claude-fable-5-2", "effort": "low"}}, {"c": "h"}, ["c.fable.1"])
        manifest = json.load(open(os.path.join(out, "manifest.json")))
        self.assertEqual(sorted(manifest["models"]), ["fable", "opus"])
        self.assertEqual(manifest["runs"], ["c.fable.1", "c.opus.1"])


class Measure(unittest.TestCase):
    def test_claude_output_gives_the_review_and_its_cost(self):
        text, meta = recall.parse_output("claude", json.dumps(CLAUDE_OUT), None)
        self.assertEqual(text, "## Findings\nnone")
        self.assertEqual(meta["cost_usd"], 1.25)
        self.assertEqual(meta["duration_ms"], 61000)
        self.assertEqual(meta["num_turns"], 7)
        self.assertEqual(meta["usage"], {"input_tokens": 10, "cache_creation_input_tokens": 2000,
                                         "cache_read_input_tokens": 30000, "output_tokens": 900})

    def test_claude_error_gives_no_review(self):
        text, _ = recall.parse_output("claude", json.dumps(dict(CLAUDE_OUT, is_error=True)), None)
        self.assertEqual(text, "")
        self.assertEqual(recall.parse_output("claude", "not json", None)[0], "")

    def test_codex_output_gives_tokens_and_no_cost(self):
        out = os.path.join(tempfile.mkdtemp(), "last.md")
        open(out, "w").write("the review")
        text, meta = recall.parse_output("codex", CODEX_OUT, out)
        self.assertEqual(text, "the review")
        self.assertIsNone(meta["cost_usd"])
        self.assertEqual(meta["usage"]["input_tokens"], 15893)
        self.assertEqual(meta["usage"]["output_tokens"], 5)

    def test_run_one_saves_the_review_and_its_measurements(self):
        out = tempfile.mkdtemp()
        path = os.path.join(out, "c.fable.1.md")
        script = f"import sys; sys.stdout.write({json.dumps(json.dumps(CLAUDE_OUT))})"
        old = recall.command
        recall.command = lambda family, model, prompt, wt, tmp, effort: [sys.executable, "-c", script]
        try:
            self.assertEqual(recall.run_one({"model": "claude-fable-5-2", "effort": "low"}, "fable", "p", out, path),
                             (path, "ok"))
        finally:
            recall.command = old
        self.assertEqual(open(path).read(), "## Findings\nnone")
        meta = json.load(open(os.path.join(out, "c.fable.1.meta.json")))
        self.assertEqual((meta["model"], meta["effort"], meta["cost_usd"]), ("claude-fable-5-2", "low", 1.25))
        self.assertIsInstance(meta["wall_s"], float)


class Report(unittest.TestCase):
    def test_report_prints_time_and_cost_per_model(self):
        out = tempfile.mkdtemp()
        case = recall.load_cases(None)[0]["id"]
        runs = [f"{case}.fable.1", f"{case}.fable.2", f"{case}.opus.1", f"{case}.opus.2"]
        json.dump({"models": {"fable": {"model": "claude-fable-5-2", "effort": "low"},
                              "opus": {"model": "claude-opus-5-5", "effort": "medium"}},
                   "prompts": {case: "h"}, "runs": runs}, open(os.path.join(out, "manifest.json"), "w"))
        for run, found, wall, cost in zip(runs, (True, False, True, True), (10, 30, 100, 200), (1.0, 3.0, 0.5, None)):
            json.dump({"found": found}, open(os.path.join(out, run + ".json"), "w"))
            json.dump({"wall_s": wall, "cost_usd": cost, "usage": {"input_tokens": 1, "output_tokens": 2}},
                      open(os.path.join(out, run + ".meta.json"), "w"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            recall.report({"out": out})
        text = buf.getvalue()
        self.assertIn("fable (low)", text)
        self.assertIn("opus (medium)", text)
        self.assertIn("fable: time mean 20s, median 20s; cost mean $2.00 per review, total $4.00 (2/2 reviews timed, 2 priced)", text)
        self.assertIn("opus: time mean 150s, median 150s; cost mean $0.50 per review, total $0.50 (2/2 reviews timed, 1 priced)", text)
        self.assertIn("fable+opus: 1/1", text)


if __name__ == "__main__":
    unittest.main()
