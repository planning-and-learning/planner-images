# Planner images

Build the images from this directory with `./build-planners.sh`. Rebuild existing
`.sif` files after changing the wrappers or definitions.

The Levitron satisficing planner is vendored in `levitron/` and builds as
`levitron_sat.sif`. Run it with `./levitron_sat.sif DOMAIN PROBLEM PLAN`;
portfolio plans use numbered suffixes such as `PLAN.1`.

All seven images report `peak_memory_mb` on stdout: peak resident set size in
decimal MB (1 MB = 1,000,000 bytes), including parsing, grounding, and search.
Validation runs outside the image and is excluded. Linux reports the maximum
individual-process RSS, including descendants waited for by the planner; this
is not the sum of simultaneously resident processes or virtual address space.

The wrapper preserves planner output and exit status and reports memory on
normal failures and catchable termination signals. Killing the whole process
group with SIGKILL can prevent reporting; missing memory must remain unknown.
Terminating a multiprocess driver before it waits for its children can also
omit those children's memory from the reported value.

Successful SIWM searches also report `choice_depth` and `choice_width` from
RunIR's first discovered goal predecessor path. Width counts admitted bindings
after effect filtering. These metrics are absent for failed searches and for
planners without module-program choices.

Check the resource wrapper and Levitron portfolio exit status without building images:

```sh
python3 -m unittest test_resources test_levitron
```
