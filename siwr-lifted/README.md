# RunIR Lifted SIWR

Lifted SIWR using `pyrunir.kr.ps.base.find_lifted_solution` with
`universal = False`.

```sh
lifted-siwr.py domain.pddl task.pddl plan.out sketch.txt
```

The four positional arguments are required. The sketch file must contain a
RunIR `(:sketch ...)` description.

The image uses `pyrunir==0.2.10`. Search has no state limit by default; pass
`--max-num-states N` to impose one.
