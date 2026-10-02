"""Exercise resource reporting without planner dependencies or images."""

import os
from pathlib import Path
import signal
import subprocess
import sys
import unittest


WRAPPER = Path(__file__).with_name("report-resources.py")


class ResourceTests(unittest.TestCase):
    def test_memory_output_and_exit_status(self):
        for status in (0, 7):
            with self.subTest(status=status):
                result = subprocess.run(
                    [sys.executable, str(WRAPPER), sys.executable, "-c",
                     "import resource, sys; data = bytearray(32 * 1024 * 1024); "
                     "print('child_rss_kib:', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss); "
                     "print('planner error', file=sys.stderr); sys.exit(int(sys.argv[1]))",
                     str(status)], capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, status)
                self.assertEqual(result.stderr, "planner error\n")
                values = dict(line.split(": ", 1) for line in result.stdout.splitlines())
                self.assertGreater(float(values["peak_memory_mb"]), 32)
                expected = int(values["child_rss_kib"]) * 1024 / 1_000_000
                # The interpreter may allocate a little more while exiting.
                self.assertGreaterEqual(float(values["peak_memory_mb"]), expected)
                self.assertLess(float(values["peak_memory_mb"]), expected + 1)

    def test_process_group_termination_still_reports_memory(self):
        with subprocess.Popen(
            [sys.executable, str(WRAPPER), sys.executable, "-u", "-c",
             "import time; data = bytearray(32 * 1024 * 1024); print('ready'); time.sleep(30)"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True,
        ) as process:
            try:
                self.assertEqual(process.stdout.readline(), "ready\n")
                os.killpg(process.pid, signal.SIGTERM)
                stdout, _ = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 128 + signal.SIGTERM)
                self.assertGreater(float(stdout.split(": ")[1]), 32)
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()


if __name__ == "__main__":
    unittest.main()
