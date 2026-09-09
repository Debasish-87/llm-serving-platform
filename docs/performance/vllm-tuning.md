# vLLM Performance Tuning

## Test Model

Qwen/Qwen2.5-0.5B-Instruct

## Hardware

GPU: NVIDIA GTX 1650  
VRAM: 4GB

---

# Parameters to Test

## 1. gpu_memory_utilization

Controls how much GPU memory vLLM is allowed to use.

Example:

```text
0.70
0.80
0.90
````

Higher values can provide more KV cache capacity, but leave less safety margin for GPU memory.

---

## 2. max_model_len

Maximum context length accepted by the model server.

Test values:

```text
512
1024
2048
```

Increasing context length increases KV cache memory requirements.

---

## 3. max_num_seqs

Maximum number of sequences that can be processed concurrently.

Test values:

```text
1
2
4
8
```

Higher concurrency may improve throughput but can increase memory pressure and latency.

---

## 4. dtype

Model precision.

Possible values:

```text
auto
float16
bfloat16
```

The correct choice depends on the GPU and model support.

---

# Benchmark Process

For every configuration:

1. Deploy vLLM
2. Run smoke test
3. Run load test
4. Record latency
5. Record throughput
6. Record GPU utilization
7. Record GPU memory
8. Check errors
9. Compare results

---

# Goal

Find the best balance between:

* Latency
* Throughput
* GPU utilization
* GPU memory usage
* Stability

````
