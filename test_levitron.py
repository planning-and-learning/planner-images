"""Check that Powerlifted reports success when any portfolio iteration solves."""

from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from levitron.ext.powerlifted.driver import portfolio_runner


class LevitronTests(unittest.TestCase):
    def test_portfolio_exit_status(self):
        options = SimpleNamespace(
            time_limit=60, iteration=["gbfs,ff,yannakakis,1"] * 2,
            plan_file="plan", translator_file="output.lifted", state="sparse",
            seed=1, validate=False, stop_after_first_plan=False,
        )
        for statuses, expected in [([0, 1], 0), ([1, 0], 0), ([1, 1], -1)]:
            with self.subTest(statuses=statuses), redirect_stdout(StringIO()), \
                    patch.object(portfolio_runner, "get_elapsed_time", return_value=1), \
                    patch.object(portfolio_runner, "remove_temporary_files"), \
                    patch.object(portfolio_runner, "run_single_search", side_effect=statuses):
                self.assertEqual(portfolio_runner.run("build", options, []), expected)


if __name__ == "__main__":
    unittest.main()
