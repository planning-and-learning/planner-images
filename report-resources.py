#!/usr/bin/env python3
"""Run a planner and report Linux peak resident memory in decimal MB."""

import resource
import signal
import subprocess
import sys


def main():
    process = subprocess.Popen(sys.argv[1:])

    def forward_signal(signum, _frame):
        # Lab signals the whole process group. Stay alive long enough to reap
        # the planner and report its memory; forwarding also handles direct signals.
        if process.poll() is None:
            try:
                process.send_signal(signum)
            except ProcessLookupError:
                pass

    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, forward_signal)
    returncode = process.wait()
    # Linux ru_maxrss is KiB; it includes descendants reaped by the planner.
    peak_mb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss * 1024 / 1_000_000
    print(f"peak_memory_mb: {peak_mb:.6f}", flush=True)
    return returncode if returncode >= 0 else 128 - returncode


if __name__ == "__main__":
    raise SystemExit(main())
