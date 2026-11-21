"""Tests for skills/retro/scripts/sessions.py: where a retro's window starts."""

import json
import os
import subprocess
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
SCRIPT = os.path.join(ROOT, "skills/retro/scripts/sessions.py")

STATE = """# Retro 2026-11-09: agent-workflow, infra, rubens

retro-window: agent-workflow 2026-10-25T21:37:16Z..2026-11-09T13:15:58Z
retro-window: infra 2026-10-26T13:16:16Z..2026-11-09T13:16:16Z
retro-window: rubens 2026-10-26T13:16:34Z..2026-11-09T13:16:34Z
"""


THREAD = [
    {"source": "user", "text": "fix the login redirect", "createdAt": "2026-11-20T15:11:06.248Z"},
    {"source": "assistant", "text": "On it.", "createdAt": "2026-11-20T15:11:14.857Z"},
    {"source": "tool", "tool": "execute", "text": "", "createdAt": "2026-11-20T15:11:19.336Z",
     "calls": [{"tool": "bash", "input": {"text": '{"command":"run-tests"}', "chars": 23},
                "result": {"text": "2 failed", "chars": 8, "is_error": True}},
               {"tool": "read", "input": {"text": '{"path":"a.ts"}', "chars": 15},
                "result": {"text": "cut", "chars": 50000, "is_error": False}},
               {"tool": "bash", "input": {"text": '{"command":"quiet-step"}', "chars": 24},
                "result": {"text": "ok", "chars": 2, "is_error": False}}]},
    {"source": "tool", "tool": "wait", "text": "Waiting for CI", "createdAt": "2026-11-20T15:12:00.000Z",
     "input": {"text": "{}", "chars": 2}, "result": {"text": "timed out", "chars": 9, "is_error": True}},
    {"source": "tool", "tool": "execute", "text": "", "createdAt": "2026-11-20T15:13:00.000Z",
     "calls": [{"tool": "bash", "input": {"text": '{"command":"last-step"}', "chars": 23},
                "result": {"text": "ok", "chars": None, "is_error": False}}],
     "result": {"text": "program stopped: call limit", "chars": 27, "is_error": True}},
]


class ThreadSkeleton(unittest.TestCase):
    def test_a_thread_export_prints_turns_calls_failures_and_oversized_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "RUBE-6.jsonl")
            with open(path, "w") as f:
                f.writelines(json.dumps(r) + "\n" for r in THREAD)
            out = subprocess.run(["python3", "-I", SCRIPT, "--skeleton", path], capture_output=True, text=True,
                                 check=True).stdout.splitlines()
        self.assertEqual(out, [
            "1 15:11 USER fix the login redirect",
            "2 15:11 SAY On it.",
            '3 15:11 CALL bash {"command":"run-tests"}',
            "3 15:11 ERROR 2 failed",
            '3 15:11 CALL read {"path":"a.ts"}',
            "3 15:11 BIG[50000 chars]",
            '3 15:11 CALL bash {"command":"quiet-step"}',
            "4 15:12 CALL wait {}",
            "4 15:12 ERROR timed out",
            '5 15:13 CALL bash {"command":"last-step"}',
            "5 15:13 ERROR program stopped: call limit",
        ])


class Window(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.state = os.path.join(self.home, ".local/state/retro")
        os.makedirs(self.state)
        self.repos = {}
        for name in ("rubens", "infra"):
            path = os.path.join(self.home, "projects", name)
            os.makedirs(path)
            subprocess.run(["git", "init", "-q", path], check=True)
            self.repos[name] = path

    def state_file(self, name, text):
        open(os.path.join(self.state, name), "w").write(text)

    def session(self, repo, sid, text, ts="2026-11-10T09:00:00Z"):
        d = os.path.join(self.home, ".claude/projects", sid)
        os.makedirs(d)
        cwd = self.repos[repo]
        rows = [
            {"type": "user", "timestamp": ts, "cwd": cwd, "message": {"role": "user", "content": "/retro"}},
            {"type": "assistant", "timestamp": ts, "cwd": cwd,
             "message": {"content": [{"type": "text", "text": text}, {"type": "tool_use", "name": "Bash", "input": {}}]}},
            {"type": "user", "timestamp": ts, "cwd": cwd, "message": {"role": "user", "content": "thanks"}},
        ]
        with open(os.path.join(d, sid + ".jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)

    def run_script(self, *repos):
        args = [a for r in repos for a in ("--repo", self.repos[r])]
        env = dict(os.environ, HOME=self.home)
        out = subprocess.run(["python3", "-I", SCRIPT, *args], env=env, capture_output=True, text=True, check=True)
        return [l.split("\t") for l in out.stdout.splitlines() if l.startswith("window\t")]

    def test_a_retro_run_elsewhere_chains_through_its_state_file(self):
        self.state_file("2026-11-09.md", STATE)
        [window] = self.run_script("rubens")
        self.assertTrue(window[1].startswith("2026-11-09T13:16:34Z.."), window)
        self.assertEqual(window[2], "last retro (2026-11-09.md)")

    def test_a_record_in_the_user_drive_chains_too(self):
        drive = os.path.join(self.home, ".capy/drive/user-leo/retro")
        os.makedirs(drive)
        open(os.path.join(drive, "2026-11-09.md"), "w").write(STATE)
        [window] = self.run_script("rubens")
        self.assertTrue(window[1].startswith("2026-11-09T13:16:34Z.."), window)

    def test_a_marker_for_another_repo_is_not_this_repos(self):
        self.state_file("2026-11-09.md", STATE.replace("retro-window: rubens", "retro-window: rubens-old"))
        [window] = self.run_script("rubens")
        self.assertTrue(window[2].startswith("default 14 days"), window)

    def test_an_in_session_marker_without_a_name_still_counts(self):
        self.session("rubens", "s1", "retro-window: 2026-11-01T00:00:00Z..2026-11-10T08:00:00Z")
        [window] = self.run_script("rubens")
        self.assertTrue(window[1].startswith("2026-11-10T08:00:00Z.."), window)
        self.assertEqual(window[2], "last retro (session s1)")

    def test_the_latest_marker_wins_across_session_and_state(self):
        self.state_file("2026-11-09.md", STATE)
        self.session("rubens", "s1", "retro-window: rubens 2026-11-01T00:00:00Z..2026-11-02T00:00:00Z")
        [window] = self.run_script("rubens")
        self.assertEqual(window[2], "last retro (2026-11-09.md)")
        self.state_file("2026-11-09.md", "")
        [window] = self.run_script("rubens")
        self.assertEqual(window[2], "last retro (session s1)")

    def test_an_in_session_marker_for_another_repo_is_skipped(self):
        self.session("rubens", "s1", "retro-window: infra 2026-11-01T00:00:00Z..2026-11-10T08:00:00Z")
        [window] = self.run_script("rubens")
        self.assertNotEqual(window[2], "last retro (session s1)")

    def test_each_repo_gets_its_own_table(self):
        self.state_file("2026-11-09.md", STATE)
        rubens, infra = self.run_script("rubens", "infra")
        self.assertTrue(rubens[1].startswith("2026-11-09T13:16:34Z.."), rubens)
        self.assertTrue(infra[1].startswith("2026-11-09T13:16:16Z.."), infra)


if __name__ == "__main__":
    unittest.main()
