#!/usr/bin/env bash
set -euo pipefail

APPTAINER_BUILD_OPTS=${APPTAINER_BUILD_OPTS:-}

build_planner() {
    local dir=$1
    local image=$2
    local def=$3
    shift 3

    (
        cd "$dir"
        # shellcheck disable=SC2086 # allow APPTAINER_BUILD_OPTS to contain flags.
        apptainer build $APPTAINER_BUILD_OPTS "$@" --force "../$image" "$def"
    )
}

build_planner siwr-ground siwr-ground.sif siwr-ground.def
build_planner siwr-lifted siwr-lifted.sif siwr-lifted.def
build_planner siwm-ground siwm-ground.sif siwm-ground.def
build_planner siwm-lifted siwm-lifted.sif siwm-lifted.def
build_planner bfws dual-bfws.sif dual-bfws.def
build_planner lama lama-first.sif lama-first.def
build_planner levitron levitron-sat.sif Apptainer.levitron-sat
build_planner levitron levitron-sat-first.sif Apptainer.levitron-sat-first

# Scorpion for every configuration (options at run time, see scorpion/README.md).
# Set CPLEX_DIR to a CPLEX installation (with include/ and lib/) to link CPLEX for
# the LP configurations; that image contains CPLEX and must not be shared.
if [ -n "${CPLEX_DIR:-}" ]; then
    build_planner scorpion scorpion.sif scorpion.def --build-arg "CPLEX_DIR=$CPLEX_DIR"
else
    build_planner scorpion scorpion.sif scorpion.def
fi
