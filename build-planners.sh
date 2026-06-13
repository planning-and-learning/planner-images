#!/usr/bin/env bash
set -euo pipefail

APPTAINER_BUILD_OPTS=${APPTAINER_BUILD_OPTS:-}

build_planner() {
    local dir=$1
    local image=$2
    local def=$3

    (
        cd "$dir"
        # shellcheck disable=SC2086 # allow APPTAINER_BUILD_OPTS to contain flags.
        apptainer build $APPTAINER_BUILD_OPTS --force "../$image" "$def"
    )
}

build_planner siwr-ground siwr-ground.sif siwr-ground.def
build_planner siwr-lifted siwr-lifted.sif siwr-lifted.def
build_planner bfws dual-bfws.sif dual-bfws.def
build_planner lama lama-first.sif lama-first.def
