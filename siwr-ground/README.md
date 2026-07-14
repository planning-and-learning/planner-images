# RunIR Ground SIWR

Ground SIWR using `pyrunir.kr.ps.base.find_ground_solution` with
`universal = False`.

```sh
ground-siwr.py domain.pddl task.pddl plan.out sketch.txt
```

The four positional arguments are required. The sketch file must contain a
RunIR `(:sketch ...)` description.
