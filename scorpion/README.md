# Scorpion

One image, `scorpion.sif`, for every Scorpion configuration: the planner
options are given at run time, after the task.

```sh
scorpion.sif DOMAIN TASK PLAN [OPTIONS]
scorpion.sif TASK.sas PLAN [OPTIONS]

scorpion.sif domain.pddl task.pddl plan --search "astar(lmcut())"
scorpion.sif domain.pddl task.pddl plan --alias scorpion
scorpion.sif domain.pddl task.pddl plan --preprocess --search "astar(scp_online([projections(systematic(2))]))"
scorpion.sif domain.pddl task.pddl plan --config pho-sys2              # a name from configs.json
scorpion.sif domain.pddl task.pddl plan --preprocess --config pho-sys2
```

`OPTIONS` are Fast Downward's: driver options such as `--preprocess` (h²
preprocessing) or `--alias NAME` first, then component options from the first of
`--search`, `--evaluator`, `--heuristic`, `--landmarks`, `--translate-options`,
`--preprocess-options` or `--search-options` on. The run is exactly
`fast-downward.py --plan-file PLAN DRIVER_OPTIONS INPUTS COMPONENT_OPTIONS`.
The second form searches an already translated task (a file starting with
`begin_version`); together with the driver's `--translate`, `--sas-file` and
`--preprocessed-sas-file` options this lets a caller translate once, inspect the
task, and then search it.

The image adds nothing of its own: no limits (the caller sets them), no
preprocessing unless `--preprocess` is given, and the task's own action costs
(pass cost-free PDDL copies for unit costs). Like every image in this
repository it reports `peak_memory_mb`.

## Default baselines: `configs.json`

[`configs.json`](configs.json) names 44 baselines with Scorpion's default
options. The image contains it: `--config NAME` stands for NAME's options and
combines with other options (`--preprocess --config lmcut`). Experiments can also
pass their own options directly.

| Name | Options |
|---|---|
| `scp-online-GEN` | `--search "astar(scp_online([projections(GEN)]))"` |
| `canonical-GEN` | `--search "astar(cpdbs(GEN))"` (`canonical-hillclimbing` is iPDB) |
| `pho-GEN` | `--search "astar(pho([projections(GEN)], saturated=true))"` |
| `ocp-GEN` | `--search "astar(ocp([projections(GEN)]))"` |
| `scorpion` | `--alias scorpion` |
| `cartesian` | `--search "astar(scp_online([cartesian()]))"` |
| `lmcut` | `--search "astar(lmcut())"` |
| `bjolp` | `--alias seq-opt-bjolp` |
| `merge-and-shrink` | SCC-DFP merging, bisimulation shrinking, `max_states=50k` (Scorpion's documented recommendation; there are no defaults) |
| `blind` | `--search "astar(blind())"` |
| `lmcut-seq` | `--search "astar(operatorcounting([state_equation_constraints(), lmcut_constraints()]))"` |
| `state-equation` | `--search "astar(operatorcounting([state_equation_constraints()]))"` |

`GEN` is one of `sys1` … `sys4` (`systematic(1)` … `systematic(4)`), `sys-scp`
(`sys_scp()`), `cegar` (`multiple_cegar()`), `hillclimbing`, `genetic` or
`random-patterns` (`random_patterns()`). Of these, only `scorpion` uses partial
order reduction, as part of Scorpion's recommended preset.

## LP solver: built with or without CPLEX

`pho`, `ocp` and `operatorcounting` solve linear programs and need CPLEX.
Scorpion links its LP solver at compile time, so this is a build choice;
`/planner/LP_SOLVER` in the image says `cplex` or `none`:

```sh
cd scorpion
apptainer build ../scorpion.sif scorpion.def                                        # no LP solver: shareable
apptainer build --build-arg CPLEX_DIR=/path/to/cplex ../scorpion.sif scorpion.def   # with CPLEX
```

`../build-planners.sh` does the same, with CPLEX when `CPLEX_DIR` is set. The
CPLEX build copies only CPLEX's `include/` and `lib/` and links the static
library, so the image needs no CPLEX files or license at run time, but it
contains CPLEX: use it for your own runs and do not share it. Without CPLEX, an
LP configuration stops at once with "Tried to use LP solver CPLEX, but the
planner was compiled without support for it".

## What is vendored

`scorpion/` is the [planning-and-learning fork](https://github.com/planning-and-learning/scorpion)
of [Scorpion](https://github.com/jendrikseipp/scorpion) at commit
`e6f052098ef7a0e9d511972803d59080c1f69273` (2026-11-10, the head of its
`scorpion` branch), unmodified: the subset `build.py`, `build_configs.py`,
`driver/`, `fast-downward.py`, `src/`, `LICENSE.md`, `README.md`, `CHANGES.md`.

The fork is upstream Scorpion at `f4f754b` (2026-10-10) plus:

- the translator option `--mutex-groups FILE`, which takes a task's FDR
  variables and mutex groups from a JSON file; pattern-database-llm-loop needs
  it for runs with tyr's variables (`sys-scp-tyr` and the learned programs);
- an h² preprocessor fix: a task that pruning leaves without variables is
  written as trivially solvable when its goal holds initially, not as
  unsolvable;
- the search algorithms `eval_plan` and `inspect_scp` and more logging for
  online saturated cost partitioning.

It lacks upstream's five later commits up to `6f1de47` (2026-11-08): CMake
dependency declarations, upstream's own fix of the same h² bug and its style
commit, CI versions, and the removal of an unused class. The two h² fixes
differ only for tasks with axioms.

The image is Ubuntu 24.04; the driver and translator run under PyPy.

To update Scorpion, replace `scorpion/` with `git archive <commit>` of the same
paths from the pinned repository, update the commit above and rebuild the image.
