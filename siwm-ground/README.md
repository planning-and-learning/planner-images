# RunIR Ground SIWM

Ground SIWM using `pyrunir.kr.ps.ext.find_ground_solution` with
`universal = False`.

```sh
ground-siwm.py domain.pddl task.pddl plan.out program.txt
```

The four positional arguments are required. The program file must contain a
RunIR `(:program ...)` module-program description.

The image uses `pyrunir==0.2.9`.
