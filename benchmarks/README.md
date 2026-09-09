# Benchmarks & Cost Analysis

This directory turns the serving platform into a measurement tool, not just a
deployment. It answers three questions that `docs/performance/vllm-tuning.md`
raises but does not close the loop on:

1. How does each serving configuration actually perform under load?
2. What does that performance cost, in GPU-hours and $/1M tokens?
3. Which configuration is the right tradeoff for a given latency budget?

---

## Layout

```text
benchmarks/
├── configs/            # One file per configuration under test
│   ├── vllm-fp16.env
│   └── vllm-awq.env
├── scripts/
│   ├── run_benchmark.sh      # Orchestrates one full benchmark run
│   ├── quantize_model.py     # Produces the AWQ-quantized model variant
│   └── collect_gpu_metrics.sh
├── k6/
│   └── benchmark-test.js     # k6 script that emits structured JSON summaries
├── results/
│   ├── SCHEMA.md
│   └── template-result.json  # Shape every result file follows
└── reports/
    └── cost-latency-tradeoff.md   # Filled in after runs complete
```

## Methodology

Each configuration is benchmarked the same way, so results are comparable:

```text
Deploy configuration
        │
        ▼
Run smoke test (correctness check)
        │
        ▼
Run k6 benchmark at fixed concurrency steps
        │
        ▼
Sample GPU metrics during the run (utilization, memory, power)
        │
        ▼
Write results/<config-name>.json
        │
        ▼
Aggregate all results into reports/cost-latency-tradeoff.md
```

Concurrency is stepped rather than fixed, so the saturation point (where p95
latency stops being linear) is visible in the results rather than assumed.

## Configurations under test

| Config | Precision | Purpose |
|---|---|---|
| `vllm-fp16` | FP16 (baseline) | Current default deployment |
| `vllm-awq`  | AWQ 4-bit | Tests whether quantization changes the latency/throughput/cost tradeoff |

Additional configs (a second engine such as TensorRT-LLM or Triton, or a
multi-GPU tensor-parallel run) can be added the same way: drop a new
`configs/<name>.env`, point `run_benchmark.sh` at it, and a new
`results/<name>.json` is produced automatically.

## Running a benchmark

```bash
# 1. Deploy the configuration under test (see configs/vllm-fp16.env for values)
kubectl apply -k k8s/serving/ -f benchmarks/configs/vllm-fp16.env

# 2. Run the benchmark
./benchmarks/scripts/run_benchmark.sh vllm-fp16

# Repeat for each configuration, then build the comparison report
```

`run_benchmark.sh` writes one file to `results/`, containing:
- Latency percentiles (p50/p90/p95/p99)
- Throughput (requests/sec and tokens/sec)
- GPU utilization and memory samples taken during the run
- Error rate

## Cost model

Cost is derived, not measured directly — it comes from the instance's
hourly GPU cost divided by observed tokens/sec:

```text
$ per 1M tokens = (GPU instance $/hour ÷ 3600) × 1,000,000 ÷ tokens/sec
```

This is intentionally simple. It assumes a single GPU fully dedicated to
the benchmark, which matches how this platform is deployed. The formula
and instance pricing assumptions are documented per-run in
`reports/cost-latency-tradeoff.md` so the numbers stay auditable rather
than being a single unexplained figure.

## What this is not

This is not a claim of production-scale benchmarking. Results here reflect
whatever hardware the run was executed on (see the `hardware` field in each
`results/*.json` file). The point is the methodology and the tradeoff
reasoning, which holds regardless of GPU class — the numbers should be
re-run on target hardware before being used for real capacity planning.
