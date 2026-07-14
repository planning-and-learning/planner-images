# RunIR Lifted SIWR

Lifted SIWR using `pyrunir.kr.ps.base.find_lifted_solution` with
`universal = False`.

```sh
lifted-siwr.py domain.pddl task.pddl plan.out sketch.txt
```

The four positional arguments are required. The sketch file must contain a
RunIR `(:sketch ...)` description.
