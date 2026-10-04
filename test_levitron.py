"""Check Levitron launcher modes and Powerlifted portfolio stopping behavior."""

from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from levitron.ext.powerlifted.driver import portfolio_runner


class LevitronTests(unittest.TestCase):
    def test_portfolio_exit_status(self):
        for first in (False, True):
            for statuses, expected in [([0, 1], 0), ([1, 0], 0), ([1, 1], -1)]:
                options = SimpleNamespace(
                    time_limit=60, iteration=["gbfs,ff,yannakakis,1"] * 2,
                    plan_file="plan", translator_file="output.lifted", state="sparse",
                    seed=1, validate=False, stop_after_first_plan=first,
                )
                with self.subTest(first=first, statuses=statuses), redirect_stdout(StringIO()), \
                        patch.object(portfolio_runner, "get_elapsed_time", return_value=1), \
                        patch.object(portfolio_runner, "remove_temporary_files"), \
                        patch.object(portfolio_runner, "run_single_search", side_effect=statuses) as search:
                    self.assertEqual(portfolio_runner.run("build", options, []), expected)
                    calls = statuses.index(0) + 1 if first and 0 in statuses else len(statuses)
                    self.assertEqual(search.call_count, calls)

    def test_launcher_flags_fallback_and_exit_status(self):
        launcher = Path(__file__).parent / "levitron/levitron-sat.sh"
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            stub = root / "pypy3"
            stub.write_text(
                f"#!{sys.executable}\n"
                "import json, os, sys\n"
                "with open(os.environ['CALLS'], 'a') as stream:\n"
                "    stream.write(json.dumps(sys.argv[1:]) + '\\n')\n"
                "key = 'MAIDU_EXIT' if sys.argv[1].endswith('/fast-downward.py') else 'LIFTED_EXIT'\n"
                "sys.exit(int(os.environ[key]))\n"
            )
            stub.chmod(0o755)
            log = root / "calls.jsonl"
            files = ["domain with spaces.pddl", "problem with spaces.pddl", "plan with spaces"]
            for first in (False, True):
                for grounded_status, lifted_status in ((0, 7), (1, 0), (1, 7)):
                    with self.subTest(first=first, grounded=grounded_status, lifted=lifted_status):
                        log.write_text("")
                        result = subprocess.run(
                            ["/bin/sh", str(launcher), *(["--first"] if first else []), *files],
                            env=dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"],
                                     CALLS=str(log), MAIDU_EXIT=str(grounded_status),
                                     LIFTED_EXIT=str(lifted_status)),
                            capture_output=True, text=True, check=False,
                        )
                        self.assertEqual(result.returncode, lifted_status if grounded_status else 0,
                                         result.stderr)
                        calls = [json.loads(line) for line in log.read_text().splitlines()]
                        self.assertEqual(len(calls), 2 if grounded_status else 1)
                        self.assertIn("seq-sat-maidu", calls[0])
                        for call, flag in zip(calls, ("--portfolio-single-plan", "--stop-after-first-plan")):
                            self.assertEqual(flag in call, first)
                            for filepath in files:
                                self.assertIn(filepath, call)


if __name__ == "__main__":
    unittest.main()
