# Cost / Latency Tradeoff Report

> Fill this in after running `scripts/run_benchmark.sh` for each
> configuration in `configs/`. Replace every `TBD` below with the value
> pulled from the corresponding `results/<config-name>.json`. Delete this
> notice once the report reflects real runs.

## Run context

| | |
|---|---|
| Date | TBD |
| Hardware | TBD (from `results/*.json` → `hardware`) |
| Model | TBD |
| k6 version | TBD |

## Summary comparison

| Config | p50 latency (ms) | p95 latency (ms) | Throughput (req/s) | GPU util (avg %) | GPU mem (avg MB) | $/1M tokens |
|---|---|---|---|---|---|---|
| vllm-fp16 | TBD | TBD | TBD | TBD | TBD | TBD |
| vllm-awq | TBD | TBD | TBD | TBD | TBD | TBD |

## Findings

> Write these after the numbers are in — do not fill in a conclusion before
> the run confirms it. Structure to follow:

1. **Latency**: Which config had lower p95 latency, and by how much? Did
   quantization change latency in the expected direction?
2. **Throughput**: Did the larger `MAX_NUM_SEQS` allowed by AWQ's smaller
   memory footprint translate into measurably higher requests/sec, or did
   something else become the bottleneck first (CPU, network, GPU compute)?
3. **Saturation point**: At which concurrency step did p95 latency stop
   scaling linearly? This is the practical capacity limit for this
   hardware/config combination.
4. **Cost**: If `GPU_COST_PER_HOUR_USD` was set to a real cloud rate, what
   is $/1M tokens for each config? Is the cheaper config also the one with
   acceptable latency for the target use case?
5. **Recommendation**: Given a hypothetical latency SLA (state one, e.g.
   "p95 < 2s"), which configuration would be selected for production, and
   why?

## Reproducing this report

```bash
./scripts/run_benchmark.sh vllm-fp16
./scripts/run_benchmark.sh vllm-awq
# then update the table above from results/*.json
```

## Limitations

- Single-GPU, single-node results. Multi-GPU tensor-parallel behavior is
  not captured here (see the roadmap in `benchmarks/README.md`).
- `approx_tokens_per_sec` is derived from a fixed `max_tokens`, not parsed
  from actual API responses — see `results/SCHEMA.md` for the caveat.
- Cost figures are only as good as the `GPU_COST_PER_HOUR_USD` value used;
  spot vs on-demand pricing will change the picture significantly.
