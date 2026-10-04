#!/bin/sh
set -eu

first_plan=
if [ "${1:-}" = "--first" ]; then
    first_plan=1
    shift
fi

DOMAINFILE="$1"
PROBLEMFILE="$2"
PLANFILE="$3"

pypy3 /planner/fast-downward.py \
    --overall-memory-limit 6G \
    --overall-time-limit 30m \
    --translate-time-limit 15m \
    --transform-task preprocess-h2 \
    --transform-task-options h2_time_limit,180 \
    --alias seq-sat-maidu \
    ${first_plan:+--portfolio-single-plan} \
    --plan-file "$PLANFILE" \
    "$DOMAINFILE" "$PROBLEMFILE" || pypy3 /planner/ext/powerlifted/powerlifted.py \
    -d "$DOMAINFILE" -i "$PROBLEMFILE" --plan-file "$PLANFILE" \
    --iteration alt-bfws1,rff,yannakakis,476 \
    --iteration alt-bfws1,add,yannakakis,38 \
    --iteration alt-bfws2,ff,yannakakis,74 \
    --iteration alt-bfws2,add,yannakakis,359 \
    --iteration lazy-po,ff,yannakakis,234 \
    --iteration bfws2,blind,yannakakis,278 \
    --iteration lazy-po,add,yannakakis,80 \
    --iteration bfws1,blind,yannakakis,116 \
    --iteration gbfs,rff,yannakakis,80 \
    --iteration gbfs,add,yannakakis,29 \
    --unit-cost --preprocess-task --only-effects-novelty-check \
    ${first_plan:+--stop-after-first-plan} \
    --time-limit 1800
