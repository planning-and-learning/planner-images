#!/usr/bin/env python3

from __future__ import annotations

import argparse
from datetime import timedelta
from pathlib import Path
from time import perf_counter

from pypddl.formalism import ParserOptions
from pyrunir.datasets import LiftedTaskSearchContext
from pyrunir.kr import LiftedTaskContext
from pyrunir.kr.dl.ext import ConstructorRepositoryFactory
from pyrunir.kr.ps.ext import (
    LiftedModuleProgramSearchOptions,
    RepositoryFactory,
    find_lifted_solution,
)
from pyrunir.kr.ps.ext.dl import parse_module_program
from pyyggdrasil.execution import ExecutionContext
from pytyr.formalism.planning import Parser
from pytyr.planning.lifted import Task


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run lifted SIWM on one PDDL task with a RunIR module program."
    )
    parser.add_argument("domain_file", type=Path)
    parser.add_argument("task_file", type=Path)
    parser.add_argument("plan_file", type=Path)
    parser.add_argument("program_file", type=Path)
    parser.add_argument("--max-num-states", type=int, default=1_000_000)
    parser.add_argument(
        "--max-time", type=float, default=None, help="Search time limit in seconds."
    )
    parser.add_argument("--num-threads", type=int, default=1)
    parser.add_argument("--random-seed", type=int, default=0)
    parser.add_argument("--shuffle-successors", action="store_true")
    parser.add_argument("--verbosity", type=int, default=1)
    args = parser.parse_args()

    if args.max_num_states < 1:
        parser.error("--max-num-states must be at least 1.")
    if args.max_time is not None and args.max_time <= 0:
        parser.error("--max-time must be greater than 0.")
    if args.num_threads < 1:
        parser.error("--num-threads must be at least 1.")

    for path_name in ("domain_file", "task_file", "program_file"):
        path = getattr(args, path_name)
        if not path.is_file():
            parser.error(f"{path_name.replace('_', ' ')} is not a file: {path}")

    return args


def format_action(action) -> str:
    name = action.get_action().get_name()
    objects = " ".join(obj.get_name() for obj in action.get_objects())
    return f"({name} {objects})" if objects else f"({name})"


def extract_plan(result):
    if not result.is_successful():
        return [], None, None
    if result.plan is None:
        raise RuntimeError("Successful SIWM search returned no plan.")

    actions = [node.label for node in result.plan.get_labeled_succ_nodes()]
    return actions, result.plan.get_cost(), result.plan.get_length()


def solve(args: argparse.Namespace):
    parser_options = ParserOptions()
    parser = Parser(args.domain_file, parser_options)
    formalism_task = parser.parse_task(args.task_file, parser_options)
    planning_domain = parser.get_domain()

    execution_context = ExecutionContext(args.num_threads)
    task = Task(formalism_task)
    search_context = LiftedTaskSearchContext(task, execution_context)
    task_context = LiftedTaskContext(search_context)
    dl_repository = ConstructorRepositoryFactory().create(task)
    program_repository = RepositoryFactory().create(dl_repository)
    program = parse_module_program(
        args.program_file.read_text(encoding="utf-8"),
        planning_domain,
        program_repository,
    )

    options = LiftedModuleProgramSearchOptions()
    options.universal = False
    options.max_num_states = args.max_num_states
    options.max_time = (
        None if args.max_time is None else timedelta(seconds=args.max_time)
    )
    options.random_seed = args.random_seed
    options.shuffle_labeled_succ_nodes = args.shuffle_successors

    search_start = perf_counter()
    result = find_lifted_solution(task_context, program, options)
    search_time = perf_counter() - search_start
    actions, plan_cost, plan_length = extract_plan(result)
    return result, actions, plan_cost, plan_length, search_time


def write_plan(
    result,
    actions: list,
    plan_cost,
    plan_length,
    plan_file: Path,
) -> None:
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    if not result.is_successful():
        plan_file.write_text(
            f"; status: {result.status.name}\n", encoding="utf-8"
        )
        return

    lines = [
        *(format_action(action) for action in actions),
        f"; cost = {plan_cost} (unit cost)",
        f"; length = {plan_length}",
    ]
    plan_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    total_start = perf_counter()
    args = parse_args()
    result, actions, plan_cost, plan_length, search_time = solve(args)
    total_time = perf_counter() - total_start
    write_plan(result, actions, plan_cost, plan_length, args.plan_file)

    print(f"status: {result.status.name}")
    if result.is_successful():
        print(f"plan_length: {plan_length}")
        print(f"plan_cost: {plan_cost}")
    print(f"search_time: {search_time:.6f}")
    print(f"total_time: {total_time:.6f}")
    print("maximum_effective_width: null")
    print("average_effective_width: null")
    print("num_solved_subsearches: 0")
    if args.verbosity > 0 and actions:
        print(*(format_action(action) for action in actions), sep="\n")
    return 0 if result.is_successful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
