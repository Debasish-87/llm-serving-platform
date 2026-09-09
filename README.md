# LLM Serving Platform

A production-style GPU-based LLM serving platform built to understand how Large Language Models are deployed, served, monitored, secured, and operated in a Kubernetes-based environment.

This project focuses on the infrastructure and operational side of LLM inference using **vLLM, Kubernetes, NVIDIA GPUs, Envoy, Prometheus, Grafana, Loki, OpenTelemetry, Tempo, Alertmanager, Helm, and k6**.

> Project Status: Under Active Development

---

## Goals

* Serve Large Language Models using vLLM
* Run inference workloads on NVIDIA GPUs
* Containerize the serving stack with Docker
* Deploy and manage workloads with Kubernetes
* Add an Envoy-based LLM Gateway layer
* Monitor platform and inference metrics using Prometheus
* Visualize metrics using Grafana
* Monitor NVIDIA GPU utilization using DCGM Exporter
* Centralize application and infrastructure logs using Fluent Bit and Loki
* Add distributed tracing using OpenTelemetry and Tempo
* Configure alerting using Prometheus Alert Rules and Alertmanager
* Perform smoke, load, and stress testing using k6
* Package Kubernetes deployments using Helm
* Build CI/CD workflows using Bitbucket Pipelines

---

## Architecture

```text
                              ┌───────────────┐
                              │    Client     │
                              │ Application   │
                              └───────┬───────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │  LLM Gateway  │
                              │     Envoy     │
                              └───────┬───────┘
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │  Kubernetes Service    │
                         │       ClusterIP        │
                         └───────────┬────────────┘
                                     │
                                     ▼
                         ┌────────────────────────┐
                         │      vLLM Pod          │
                         │                        │
                         │  Qwen 2.5 0.5B Model   │
                         │                        │
                         │      vLLM Server       │
                         └───────────┬────────────┘
                                     │
                                     ▼
                              ┌───────────────┐
                              │  NVIDIA GPU   │
                              └───────────────┘
```

---

## Request Flow

```text
Client
  │
  │ POST /v1/chat/completions
  ▼
Envoy Gateway
  │
  │ Routes Request
  ▼
vLLM Kubernetes Service
  │
  │ Routes to Healthy Pod
  ▼
vLLM Pod
  │
  │ GPU Inference
  ▼
LLM Model
  │
  ▼
Generated Response
  │
  ▼
Client
```

---

## vLLM Serving Configuration

Current model configuration:

```text
Model:
Qwen/Qwen2.5-0.5B-Instruct

GPU Memory Utilization:
80%

Maximum Model Length:
1024

Maximum Concurrent Sequences:
2
```

The vLLM workload is configured with:

```text
CPU Request:       1 CPU
CPU Limit:         2 CPU

Memory Request:    2Gi
Memory Limit:      4Gi

NVIDIA GPU:        1
```

---

## Kubernetes Architecture

The platform runs inside the `llm-serving` Kubernetes namespace.

```text
Kubernetes Cluster
│
└── llm-serving Namespace
    │
    ├── Gateway
    │   ├── Envoy Deployment
    │   └── Gateway Service
    │
    ├── LLM Serving
    │   ├── vLLM Deployment
    │   └── vLLM Service
    │
    ├── Monitoring
    │   ├── Prometheus
    │   ├── Grafana
    │   └── DCGM Exporter
    │
    ├── Logging
    │   ├── Fluent Bit
    │   └── Loki
    │
    ├── Tracing
    │   ├── OpenTelemetry Collector
    │   └── Tempo
    │
    └── Alerting
        ├── Prometheus Alert Rules
        └── Alertmanager
```

---

## Monitoring Architecture

```text
vLLM ────────────────┐
                     │
Envoy ───────────────┼────► Prometheus ────► Grafana
                     │
DCGM Exporter ───────┘
```

Prometheus collects metrics from:

* vLLM
* Envoy Gateway
* NVIDIA GPUs through DCGM Exporter
* Prometheus itself

Grafana provides visualization for:

* GPU utilization
* GPU memory usage
* GPU temperature
* GPU power usage
* vLLM running requests
* Waiting requests
* Token throughput
* Platform metrics

---

## Logging Architecture

```text
Kubernetes Pods
       │
       │ stdout / stderr
       ▼
Fluent Bit DaemonSet
       │
       ▼
      Loki
       │
       ▼
    Grafana
```

Fluent Bit collects logs from Kubernetes workloads and forwards them to Loki for centralized storage and querying.

---

## Distributed Tracing

```text
Application / Gateway
        │
        │ Trace Data
        ▼
OpenTelemetry Collector
        │
        ▼
       Tempo
        │
        ▼
      Grafana
```

The tracing stack is intended to provide visibility into request flow and latency across platform components.

---

## Alerting Architecture

```text
Prometheus Metrics
        │
        ▼
Prometheus Alert Rules
        │
        ▼
   Alertmanager
        │
        ▼
Notification Receiver
```

The platform includes alerting components for detecting operational issues and abnormal platform behavior.

---

## Deployment Strategy

The vLLM Deployment uses a Rolling Update strategy.

```text
Current vLLM Pod
        │
        │ Deployment Update
        ▼
Kubernetes Rolling Update
        │
        ├── maxUnavailable: 0
        └── maxSurge: 1
                │
                ▼
          New vLLM Pod
                │
                ▼
           Model Loading
                │
                ▼
          Startup Probe
                │
                ▼
         Readiness Probe
                │
                ▼
           Receives Traffic
                │
                ▼
           Old Pod Removed
```

> Note: GPU workloads require careful rollout planning because `maxSurge: 1` may require additional GPU capacity during deployment.

---

## Health Checks

The vLLM Deployment includes:

### Startup Probe

Ensures Kubernetes waits for the model and vLLM server to initialize before considering the container startup process complete.

### Readiness Probe

Ensures traffic is only sent to a healthy and ready vLLM instance.

### Liveness Probe

Allows Kubernetes to restart the container if it becomes unhealthy.

---

## Security

The vLLM workload currently includes container security hardening:

```text
runAsNonRoot: true

allowPrivilegeEscalation: false

Linux Capabilities:
DROP ALL
```

The deployment also includes a graceful shutdown period:

```text
terminationGracePeriodSeconds: 120
```

---

## Helm Deployment

The project includes a Helm chart for packaging and deploying the vLLM serving workload.

```text
helm/
└── vllm-serving/
    ├── Chart.yaml
    ├── values.yaml
    │
    └── templates/
        ├── deployment.yaml
        ├── service.yaml
        └── _helpers.tpl
```

Helm allows configuration to be separated from Kubernetes templates.

```text
values.yaml
      │
      ▼
Helm Templates
      │
      ▼
Rendered Kubernetes Manifests
      │
      ▼
Kubernetes Cluster
```

Validate the chart:

```bash
helm lint ./helm/vllm-serving
```

Render Kubernetes manifests:

```bash
helm template test-release ./helm/vllm-serving
```

---

## Load Testing

The platform includes k6-based performance tests.

```text
k6
│
├── Smoke Test
│
├── Load Test
│
└── Stress Test
        │
        ▼
   Envoy Gateway
        │
        ▼
     vLLM Service
        │
        ▼
      vLLM Pod
        │
        ▼
    GPU Inference
```

### Smoke Test

Verifies that the basic serving path works correctly.

### Load Test

Measures platform behavior under expected traffic.

### Stress Test

Pushes the system beyond expected traffic levels to identify bottlenecks and failure points.

---

## Development Environment

```text
Host System
│
├── Windows 11
│
├── WSL2
│   └── Ubuntu
│
└── VS Code
```

---

## Runtime Environment

```text
Docker
│
▼
Kubernetes
│
├── NVIDIA GPU
│
├── vLLM
│
├── Envoy Gateway
│
├── Prometheus
│
├── Grafana
│
├── Loki
│
├── Fluent Bit
│
├── OpenTelemetry
│
├── Tempo
│
└── Alertmanager
```

---

## Project Structure

```text
llm-serving-platform
│
├── docker/
│   └── vllm.Dockerfile
│
├── gateway/
│   └── envoy/
│       └── envoy.yaml
│
├── helm/
│   └── vllm-serving/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│
├── k8s/
│   ├── base/
│   │   ├── configmap.yaml
│   │   └── namespace.yaml
│   │
│   ├── gateway/
│   │   ├── envoy-config.yaml
│   │   ├── gateway-deployment.yaml
│   │   └── gateway-service.yaml
│   │
│   ├── observability/
│   │   ├── alertmanager/
│   │   │   ├── alertmanager-config.yaml
│   │   │   ├── alertmanager-deployment.yaml
│   │   │   └── alertmanager-service.yaml
│   │   │
│   │   ├── fluent-bit/
│   │   │   ├── fluent-bit-config.yaml
│   │   │   ├── fluent-bit-daemonset.yaml
│   │   │   ├── fluent-bit-rbac.yaml
│   │   │   └── fluent-bit-serviceaccount.yaml
│   │   │
│   │   ├── gpu/
│   │   │   ├── dcgm-exporter-daemonset.yaml
│   │   │   └── dcgm-exporter-service.yaml
│   │   │
│   │   ├── grafana/
│   │   │   ├── grafana-dashboard-provider.yaml
│   │   │   ├── grafana-dashboards.yaml
│   │   │   ├── grafana-datasource.yaml
│   │   │   ├── grafana-deployment.yaml
│   │   │   └── grafana-service.yaml
│   │   │
│   │   ├── loki/
│   │   │   ├── loki-config.yaml
│   │   │   ├── loki-deployment.yaml
│   │   │   └── loki-service.yaml
│   │   │
│   │   ├── otel/
│   │   │   ├── otel-collector-config.yaml
│   │   │   ├── otel-collector-deployment.yaml
│   │   │   └── otel-collector-service.yaml
│   │   │
│   │   ├── prometheus/
│   │   │   ├── prometheus-alert-rules.yaml
│   │   │   ├── prometheus-config.yaml
│   │   │   ├── prometheus-deployment.yaml
│   │   │   └── prometheus-service.yaml
│   │   │
│   │   └── tempo/
│   │       ├── tempo-config.yaml
│   │       ├── tempo-deployment.yaml
│   │       └── tempo-service.yaml
│   │
│   └── serving/
│       ├── deployment.yaml
│       └── service.yaml
│
├── load-tests/
│   └── k6/
│       ├── smoke-test.js
│       ├── load-test.js
│       └── stress-test.js
│
├── monitoring/
│   ├── opentelemetry/
│   └── prometheus/
│       └── prometheus.yml
│
├── docs/
│   └── performance/
│       └── vllm-tuning.md
│
├── scripts/
│   ├── deploy/
│   │   └── deploy.sh
│   ├── setup/
│   └── test/
│
├── docker-compose.yml
│
└── README.md
```

---

## Core Technologies

| Technology    | Purpose                          |
| ------------- | -------------------------------- |
| vLLM          | High-performance LLM inference   |
| NVIDIA GPU    | Accelerated model inference      |
| Docker        | Containerization                 |
| Kubernetes    | Container orchestration          |
| Envoy         | Gateway and request routing      |
| Prometheus    | Metrics collection               |
| Grafana       | Monitoring and visualization     |
| DCGM Exporter | NVIDIA GPU metrics               |
| Fluent Bit    | Log collection                   |
| Loki          | Centralized logging              |
| OpenTelemetry | Telemetry collection             |
| Tempo         | Distributed tracing              |
| Alertmanager  | Alert management                 |
| Helm          | Kubernetes application packaging |
| k6            | Load and performance testing     |

---

## What This Project Demonstrates

This project is designed to demonstrate practical understanding of:

* LLM inference infrastructure
* GPU-based model serving
* Kubernetes workload deployment
* LLM gateway architecture
* Observability for AI infrastructure
* GPU monitoring
* Centralized logging
* Distributed tracing
* Alerting
* Load testing
* Performance tuning
* Helm-based deployment

---

## Getting Started

Validate the Helm chart:

```bash
cd helm/vllm-serving

helm lint .
```

Render the Kubernetes manifests:

```bash
helm template test-release .
```

Check the Kubernetes cluster:

```bash
kubectl get nodes
```

Check GPU availability:

```bash
nvidia-smi
```

---

## Key Learning Focus

The goal of this project is not just to deploy an LLM.

The goal is to understand the complete operational lifecycle:

```text
Build
  ↓
Containerize
  ↓
Deploy
  ↓
Schedule on GPU
  ↓
Serve Requests
  ↓
Monitor
  ↓
Log
  ↓
Trace
  ↓
Alert
  ↓
Load Test
  ↓
Find Bottlenecks
  ↓
Tune Performance
```

This is the foundation of an **LLM Inference / AI Infrastructure Engineering** workflow.