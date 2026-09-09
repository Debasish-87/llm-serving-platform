# Results Schema

Every `results/<config-name>.json` is produced by
`scripts/build_result.py` and follows this shape. See
`template-result.json` for a fully worked (fabricated) example.

| Field | Meaning |
|---|---|
| `config_name` | Matches the `configs/<name>.env` file used |
| `timestamp` | UTC time the run started |
| `model` | HF model id served during this run |
| `quantization` | `none`, `awq`, `gptq`, etc. |
| `hardware.gpu_model` / `gpu_vram_gb` | Actual GPU the run executed on — **results are not comparable across different hardware** |
| `vllm_params` | The vLLM launch flags in effect for this run |
| `load_profile` | The k6 concurrency steps and step duration used |
| `results.total_requests` | Total requests sent across all steps |
| `results.failed_request_rate` | Fraction of requests that failed (non-200 or check failure) |
| `results.requests_per_sec` | Overall throughput across the run |
| `results.latency_ms.{p50,p90,p95,p99,max}` | Request latency distribution |
| `results.gpu.gpu_utilization_pct` | `{avg, max}` sampled once/sec during the run |
| `results.gpu.gpu_memory_used_mb` | `{avg, max}` |
| `results.approx_tokens_per_sec` | `requests_per_sec × 100` (max_tokens is fixed in the benchmark script — see note below) |
| `cost.gpu_cost_per_hour_usd` | From the config file; `0` means local/owned hardware |
| `cost.cost_per_million_tokens_usd` | `null` unless `gpu_cost_per_hour_usd > 0` |

## Known approximation

`approx_tokens_per_sec` multiplies request throughput by the fixed
`max_tokens: 100` set in `k6/benchmark-test.js`. It does **not** parse the
actual token count from each response. This is accurate only insofar as
most completions run close to the max_tokens cap. For a materially more
accurate number, extend `benchmark-test.js` to read
`response.usage.completion_tokens` from the API response and aggregate
that instead — left as a deliberate next step rather than done here, since
it requires the served model's OpenAI-compatible endpoint to actually
populate `usage` (not all serving configs do this consistently).
