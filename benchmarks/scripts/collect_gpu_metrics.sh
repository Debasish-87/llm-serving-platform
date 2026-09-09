#!/usr/bin/env bash
#
# Samples GPU utilization, memory, and power draw once per second via
# nvidia-smi and writes a CSV. Run this alongside the k6 benchmark, not
# instead of it — run_benchmark.sh starts and stops this automatically.
#
# Usage:
#   ./collect_gpu_metrics.sh <output-csv-path> <duration-seconds>
#
# For clusters already running the platform's DCGM exporter
# (k8s/observability/gpu/dcgm-exporter-daemonset.yaml), prefer querying
# Prometheus directly over this script — it gives the same data without
# needing shell access to the GPU node:
#
#   curl -s "http://<prometheus>:9090/api/v1/query_range?query=DCGM_FI_DEV_GPU_UTIL&start=<start>&end=<end>&step=1s"
#
# This script exists for local/dev runs where Prometheus isn't deployed yet.

set -euo pipefail

OUTPUT_CSV="${1:?Usage: collect_gpu_metrics.sh <output-csv-path> <duration-seconds>}"
DURATION="${2:?Usage: collect_gpu_metrics.sh <output-csv-path> <duration-seconds>}"

if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "nvidia-smi not found on PATH. Are you running this on the GPU host?" >&2
    exit 1
fi

echo "timestamp,gpu_util_pct,mem_used_mb,mem_total_mb,power_draw_w,temp_c" > "$OUTPUT_CSV"

END=$((SECONDS + DURATION))
while [ "$SECONDS" -lt "$END" ]; do
    nvidia-smi \
        --query-gpu=timestamp,utilization.gpu,memory.used,memory.total,power.draw,temperature.gpu \
        --format=csv,noheader,nounits \
        | sed 's/, /,/g' >> "$OUTPUT_CSV"
    sleep 1
done

echo "GPU metrics written to $OUTPUT_CSV"
