#!/usr/bin/env python3
"""
Combines a k6 summary JSON, a GPU metrics CSV, and the run's config file
into a single results/<config-name>.json matching results/SCHEMA.md.

Called by run_benchmark.sh — not usually run directly.
"""

import argparse
import csv
import json
from pathlib import Path


def parse_env_file(path: Path) -> dict:
    values = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def summarize_gpu_csv(path: Path) -> dict:
    if not path.exists():
        return {"samples": 0}

    util, mem_used, power, temp = [], [], [], []
    with path.open() as f:
        for row in csv.DictReader(f):
            try:
                util.append(float(row["gpu_util_pct"]))
                mem_used.append(float(row["mem_used_mb"]))
                power.append(float(row["power_draw_w"]))
                temp.append(float(row["temp_c"]))
            except (KeyError, ValueError):
                continue

    def avg_max(values):
        if not values:
            return {"avg": None, "max": None}
        return {"avg": round(sum(values) / len(values), 1), "max": round(max(values), 1)}

    return {
        "samples": len(util),
        "gpu_utilization_pct": avg_max(util),
        "gpu_memory_used_mb": avg_max(mem_used),
        "power_draw_w": avg_max(power),
        "temperature_c": avg_max(temp),
    }


def extract_k6_metrics(k6_summary: dict) -> dict:
    metrics = k6_summary.get("metrics", {})

    def get(name, field, default=None):
        return metrics.get(name, {}).get(field, default)

    total_requests = get("http_reqs", "count", 0)
    test_duration_s = get("http_reqs", "rate", 0)
    # k6's http_reqs "rate" is requests/sec already; derive duration defensively.
    duration_s = (total_requests / test_duration_s) if test_duration_s else None

    return {
        "total_requests": total_requests,
        "failed_request_rate": get("http_req_failed", "value"),
        "requests_per_sec": get("http_reqs", "rate"),
        "latency_ms": {
            "p50": get("http_req_duration", "med"),
            "p90": get("http_req_duration", "p(90)"),
            "p95": get("http_req_duration", "p(95)"),
            "p99": get("http_req_duration", "p(99)"),
            "max": get("http_req_duration", "max"),
        },
        "approx_duration_s": duration_s,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--k6-summary", required=True, type=Path)
    parser.add_argument("--gpu-csv", required=True, type=Path)
    parser.add_argument("--timestamp", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    config = parse_env_file(args.config)

    k6_summary = {}
    if args.k6_summary.exists():
        k6_summary = json.loads(args.k6_summary.read_text())
    else:
        print(f"warning: no k6 summary found at {args.k6_summary}")

    k6_metrics = extract_k6_metrics(k6_summary)
    gpu_metrics = summarize_gpu_csv(args.gpu_csv)

    tokens_per_sec = None
    cost_per_million_tokens_usd = None
    gpu_cost_per_hour = float(config.get("GPU_COST_PER_HOUR_USD", "0") or 0)
    if k6_metrics["requests_per_sec"] and gpu_cost_per_hour > 0:
        # max_tokens is fixed per request in the benchmark script (see k6/benchmark-test.js);
        # this is an approximation, not a token-accurate count from the API response.
        assumed_tokens_per_request = 100
        tokens_per_sec = k6_metrics["requests_per_sec"] * assumed_tokens_per_request
        cost_per_million_tokens_usd = round(
            (gpu_cost_per_hour / 3600) * 1_000_000 / tokens_per_sec, 4
        )

    result = {
        "config_name": config.get("CONFIG_NAME"),
        "timestamp": args.timestamp,
        "model": config.get("MODEL"),
        "quantization": config.get("QUANTIZATION", "none"),
        "hardware": {
            "gpu_model": config.get("GPU_MODEL"),
            "gpu_vram_gb": config.get("GPU_VRAM_GB"),
        },
        "vllm_params": {
            "dtype": config.get("DTYPE"),
            "gpu_memory_utilization": config.get("GPU_MEMORY_UTILIZATION"),
            "max_model_len": config.get("MAX_MODEL_LEN"),
            "max_num_seqs": config.get("MAX_NUM_SEQS"),
        },
        "load_profile": {
            "concurrency_steps": config.get("CONCURRENCY_STEPS"),
            "step_duration": config.get("STEP_DURATION"),
        },
        "results": {
            **k6_metrics,
            "gpu": gpu_metrics,
            "approx_tokens_per_sec": round(tokens_per_sec, 1) if tokens_per_sec else None,
        },
        "cost": {
            "gpu_cost_per_hour_usd": gpu_cost_per_hour,
            "cost_per_million_tokens_usd": cost_per_million_tokens_usd,
            "note": (
                "cost_per_million_tokens_usd is null when GPU_COST_PER_HOUR_USD is 0 "
                "(e.g. local/owned hardware). Set it in the config file to a real "
                "cloud on-demand or spot rate to populate this."
            ),
        },
    }

    args.output.write_text(json.dumps(result, indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
