#!/usr/bin/env bash
#
# Runs one complete benchmark for a given configuration and writes
# results/<config-name>.json
#
# Usage:
#   ./run_benchmark.sh <config-name>
#   ./run_benchmark.sh vllm-fp16
#
# Prerequisites:
#   - The corresponding k8s deployment for <config-name> is already applied
#     and the pod is Ready (see k8s/serving/deployment.yaml)
#   - k6 is installed (https://k6.io/docs/get-started/installation/)
#   - BASE_URL points at the Envoy gateway or the vLLM service directly

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_DIR="$(dirname "$SCRIPT_DIR")"

CONFIG_NAME="${1:?Usage: run_benchmark.sh <config-name>, e.g. vllm-fp16}"
CONFIG_FILE="$BENCH_DIR/configs/${CONFIG_NAME}.env"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "No config found at $CONFIG_FILE" >&2
    exit 1
fi

# shellcheck disable=SC1090
source "$CONFIG_FILE"

BASE_URL="${BASE_URL:-http://localhost:8080}"
RESULTS_DIR="$BENCH_DIR/results"
RUN_TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
GPU_CSV="$RESULTS_DIR/${CONFIG_NAME}.gpu.csv"
K6_SUMMARY_JSON="$RESULTS_DIR/${CONFIG_NAME}.k6.json"
FINAL_RESULT_JSON="$RESULTS_DIR/${CONFIG_NAME}.json"

mkdir -p "$RESULTS_DIR"

echo "=== Benchmarking $CONFIG_NAME against $BASE_URL ==="

echo "--- Smoke test ---"
k6 run --env BASE_URL="$BASE_URL" "$BENCH_DIR/../load-tests/k6/smoke-test.js"

# Rough total duration: number of concurrency steps * step duration + ramp overhead.
STEP_COUNT=$(echo "$CONCURRENCY_STEPS" | tr ',' '\n' | wc -l | tr -d ' ')
STEP_SECONDS=$(echo "$STEP_DURATION" | sed 's/s$//')
TOTAL_GPU_SAMPLE_SECONDS=$((STEP_COUNT * STEP_SECONDS + 30))

echo "--- Starting GPU metric collection (${TOTAL_GPU_SAMPLE_SECONDS}s) ---"
"$SCRIPT_DIR/collect_gpu_metrics.sh" "$GPU_CSV" "$TOTAL_GPU_SAMPLE_SECONDS" &
GPU_COLLECTOR_PID=$!

echo "--- Load benchmark ---"
k6 run \
    --env BASE_URL="$BASE_URL" \
    --env MODEL="$MODEL" \
    --env CONCURRENCY_STEPS="$CONCURRENCY_STEPS" \
    --env STEP_DURATION="$STEP_DURATION" \
    --summary-export="$K6_SUMMARY_JSON" \
    "$BENCH_DIR/k6/benchmark-test.js"

wait "$GPU_COLLECTOR_PID" 2>/dev/null || true

echo "--- Aggregating results ---"
python3 "$SCRIPT_DIR/build_result.py" \
    --config "$CONFIG_FILE" \
    --k6-summary "$K6_SUMMARY_JSON" \
    --gpu-csv "$GPU_CSV" \
    --timestamp "$RUN_TIMESTAMP" \
    --output "$FINAL_RESULT_JSON"

echo "=== Done: $FINAL_RESULT_JSON ==="
