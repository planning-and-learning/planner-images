# RunIR Ground SIWM

Ground SIWM using `pyrunir.kr.ps.ext.find_ground_solution` with
`universal = False`.

```sh
ground-siwm.py domain.pddl task.pddl plan.out program.txt
```

The four positional arguments are required. The program file must contain a
RunIR `(:program ...)` module-program description.

The image uses `pyrunir==0.2.11`. Search has no state limit by default; pass
`--max-num-states N` to impose one.

Use `--state-memorization NONE` (the default) to avoid memoizing completed
program states, or `--state-memorization CHOICE` to intern and memoize states
at admitted Choose rules. Both modes retain the returned path without keeping
the full explored graph.

Use `--state-memorization ALL` to intern and memoize every admitted program
state and retain the full explored graph.

```sh
ground-siwm.py domain.pddl task.pddl plan.out program.txt --state-memorization CHOICE
```

Successful searches report `choice_depth` and `choice_width` from RunIR: the
number of nontrivial choices and maximum admitted choice width along the first
discovered goal predecessor path, after effect filtering. Image runs also report
`peak_memory_mb`; see [resource reporting](../README.md).
