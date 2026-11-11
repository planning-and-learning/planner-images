#!/usr/bin/env python3
"""Run Scorpion on one task with the options given on the command line.

    scorpion.sif DOMAIN TASK PLAN [OPTIONS]
    scorpion.sif TASK.sas PLAN [OPTIONS]

The second form searches an already translated task (a file whose first line
is `begin_version`, as the driver decides). OPTIONS are Fast Downward's: driver
options (such as --preprocess or --alias NAME) first, then component options
from the first of --search, --evaluator, --heuristic, --landmarks,
--translate-options, --preprocess-options or --search-options on. `--config
NAME` stands for the options of NAME in configs.json. The run is

    fast-downward.py --plan-file PLAN DRIVER_OPTIONS INPUTS COMPONENT_OPTIONS
"""

import json
import os
import sys

DRIVER = ["pypy3", "/planner/fast-downward.py"]
CONFIGS = "/planner/configs.json"
COMPONENT_OPTIONS = {
    "--search",
    "--evaluator",
    "--heuristic",
    "--landmarks",
    "--translate-options",
    "--preprocess-options",
    "--search-options",
}
USAGE = "usage: scorpion.sif DOMAIN TASK PLAN [OPTIONS]  or  scorpion.sif TASK.sas PLAN [OPTIONS]"


def is_translated(path: str) -> bool:
    try:
        with open(path) as stream:
            return next(stream, "").rstrip() == "begin_version"
    except OSError:
        return False


def expand_configs(options: list[str]) -> list[str]:
    """Replace each `--config NAME` with the options of NAME in configs.json."""
    result: list[str] = []
    index = 0
    while index < len(options):
        if options[index] != "--config":
            result.append(options[index])
            index += 1
            continue
        if index + 1 == len(options):
            sys.exit(f"--config needs a name from {CONFIGS}")
        with open(CONFIGS) as stream:
            configs = json.load(stream)["configs"]
        name = options[index + 1]
        if name not in configs:
            sys.exit(f"unknown configuration {name!r}; {CONFIGS} has: {', '.join(sorted(configs))}")
        result += configs[name]["options"]
        index += 2
    return result


def main() -> None:
    arguments = sys.argv[1:]
    if len(arguments) >= 2 and is_translated(arguments[0]):
        inputs, plan, options = arguments[:1], arguments[1], arguments[2:]
    elif len(arguments) >= 3:
        inputs, plan, options = arguments[:2], arguments[2], arguments[3:]
    else:
        sys.exit(USAGE)
    options = expand_configs(options)
    first = next((i for i, option in enumerate(options) if option in COMPONENT_OPTIONS), len(options))
    command = [*DRIVER, "--plan-file", plan, *options[:first], *inputs, *options[first:]]
    sys.stdout.flush()
    os.execvp(command[0], command)


if __name__ == "__main__":
    main()
