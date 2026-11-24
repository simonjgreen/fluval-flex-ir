#!/bin/sh
set -eu

project=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
exec docker run --rm --network none --read-only --tmpfs /tmp --tmpfs /config \
    --mount "type=bind,src=$project/custom_components,dst=/project/custom_components,readonly" \
    --mount "type=bind,src=$project/tests,dst=/project/tests,readonly" \
    --entrypoint python ghcr.io/home-assistant/home-assistant:2026.11.1 \
    -B /project/tests/test_integration.py "$@"
