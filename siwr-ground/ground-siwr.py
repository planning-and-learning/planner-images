#!/usr/bin/env python3

from __future__ import annotations

import argparse
from datetime import timedelta
from pathlib import Path
from time import perf_counter

from pypddl.formalism import ParserOptions
from pyrunir.datasets import GroundTaskSearchContext
from pyrunir.kr import GroundTaskContext
from pyrunir.kr.dl.base.semantics import ConstructorRepositoryFactory
from pyrunir.kr.ps.base import (
    GroundSketchSearchOptions,
    RepositoryFactory,
    find_ground_solution,
)
from pyrunir.kr.ps.base.dl import parse_sketch
from pyyggdrasil.execution import ExecutionContext
from pytyr.formalism.planning import Parser
from pytyr.planning.lifted import (
    GroundTaskInstantiationOptions,
    GroundTaskInstantiationStatus,
    Task,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ground SIWR on one PDDL task with a RunIR sketch."
    )
    parser.add_argument("domain_file", type=Path)
    parser.add_argument("task_file", type=Path)
    parser.add_argument("plan_file", type=Path)
    parser.add_argument("sketch_file", type=Path)
    parser.add_argument("--max-num-states", type=int, default=1_000_000)
    parser.add_argument(
        "--max-time", type=float, default=None, help="Search time limit in seconds."
    )
    parser.add_argument("--num-threads", type=int, default=1)
    parser.add_argument("--random-seed", type=int, default=0)
    parser.add_argument("--shuffle-successors", action="store_true")
    parser.add_argument("--enable-invariant-synthesis", action="store_true")
    parser.add_argument("--verbosity", type=int, default=1)
    args = parser.parse_args()

    if args.max_num_states < 1:
        parser.error("--max-num-states must be at least 1.")
    if args.max_time is not None and args.max_time <= 0:
        parser.error("--max-time must be greater than 0.")
    if args.num_threads < 1:
        parser.error("--num-threads must be at least 1.")

    for path_name in ("domain_file", "task_file", "sketch_file"):
        path = getattr(args, path_name)
        if not path.is_file():
            parser.error(f"{path_name.replace('_', ' ')} is not a file: {path}")

    return args


def format_action(action) -> str:
    name = action.get_action().get_name()
    objects = " ".join(obj.get_name() for obj in action.get_objects())
    return f"({name} {objects})" if objects else f"({name})"


def extract_actions(result) -> list:
    if not result.is_successful():
        return []

    graph = result.graph
    initial_vertices = [
        vertex
        for vertex in graph.get_vertex_indices()
        if graph.get_vertex_property(vertex).is_initial
    ]
    if len(initial_vertices) != 1:
        raise RuntimeError(
            f"Expected one initial proof vertex, found {len(initial_vertices)}."
        )

    actions = []
    seen = set()
    vertex = initial_vertices[0]
    while not graph.get_vertex_property(vertex).is_goal:
        if vertex in seen:
            raise RuntimeError("SIWR proof graph contains a cycle.")
        seen.add(vertex)

        out_edges = list(graph.get_out_edge_indices(vertex))
        if len(out_edges) != 1:
            raise RuntimeError(
                "Expected a single proof path with universal search disabled, "
                f"found {len(out_edges)} outgoing edges."
            )

        edge = out_edges[0]
        actions.append(graph.get_edge_property(edge).transition.action)
        vertex = graph.get_target(edge)

    return actions


def solve(args: argparse.Namespace):
    parser_options = ParserOptions()
    parser = Parser(args.domain_file, parser_options)
    formalism_task = parser.parse_task(args.task_file, parser_options)
    planning_domain = parser.get_domain()

    execution_context = ExecutionContext(args.num_threads)
    lifted_task = Task(formalism_task)
    instantiation_options = GroundTaskInstantiationOptions(
        not args.enable_invariant_synthesis
    )
    ground_result = lifted_task.instantiate_ground_task(
        execution_context, instantiation_options
    )
    if ground_result.status != GroundTaskInstantiationStatus.SUCCESS:
        raise RuntimeError(f"Grounding failed: {ground_result.status.name}")

    search_context = GroundTaskSearchContext(ground_result.task, execution_context)
    task_context = GroundTaskContext(search_context)
    dl_repository = ConstructorRepositoryFactory().create(planning_domain)
    sketch_repository = RepositoryFactory().create(dl_repository)
    sketch = parse_sketch(
        args.sketch_file.read_text(encoding="utf-8"),
        planning_domain,
        sketch_repository,
    )

    options = GroundSketchSearchOptions()
    options.universal = False
    options.max_num_states = args.max_num_states
    options.max_time = (
        None if args.max_time is None else timedelta(seconds=args.max_time)
    )
    options.random_seed = args.random_seed
    options.shuffle_labeled_succ_nodes = args.shuffle_successors

    search_start = perf_counter()
    result = find_ground_solution(task_context, sketch, options)
    search_time = perf_counter() - search_start
    return result, extract_actions(result), search_time


def write_plan(result, actions: list, plan_file: Path) -> None:
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    if not result.is_successful():
        plan_file.write_text(
            f"; status: {result.status.name}\n", encoding="utf-8"
        )
        return

    lines = [
        *(format_action(action) for action in actions),
        f"; cost = {len(actions)} (unit cost)",
        f"; length = {len(actions)}",
    ]
    plan_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    total_start = perf_counter()
    args = parse_args()
    result, actions, search_time = solve(args)
    total_time = perf_counter() - total_start
    write_plan(result, actions, args.plan_file)

    print(f"status: {result.status.name}")
    if result.is_successful():
        print(f"plan_length: {len(actions)}")
        print(f"plan_cost: {len(actions)}")
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
