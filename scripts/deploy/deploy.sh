#!/usr/bin/env bash

set -euo pipefail

echo "========================================"
echo "Deploying LLM Serving Platform"
echo "========================================"

echo ""
echo "[1/6] Creating namespace and base resources..."
kubectl apply -f k8s/base/

echo ""
echo "[2/6] Deploying GPU monitoring..."
kubectl apply -f k8s/observability/gpu/

echo ""
echo "[3/6] Deploying observability stack..."

echo "Deploying Prometheus..."
kubectl apply -f k8s/observability/prometheus/

echo "Deploying Loki..."
kubectl apply -f k8s/observability/loki/

echo "Deploying Tempo..."
kubectl apply -f k8s/observability/tempo/

echo "Deploying OpenTelemetry Collector..."
kubectl apply -f k8s/observability/otel/

echo "Deploying Fluent Bit..."
kubectl apply -f k8s/observability/fluent-bit/

echo "Deploying Grafana..."
kubectl apply -f k8s/observability/grafana/

echo "Deploying Alertmanager..."
kubectl apply -f k8s/observability/alertmanager/

echo ""
echo "[4/6] Deploying vLLM serving..."
kubectl apply -f k8s/serving/

echo ""
echo "[5/6] Deploying LLM Gateway..."
kubectl apply -f k8s/gateway/

echo ""
echo "[6/6] Waiting for deployments..."

kubectl rollout status deployment/prometheus \
  -n llm-serving --timeout=120s || true

kubectl rollout status deployment/grafana \
  -n llm-serving --timeout=120s || true

kubectl rollout status deployment/vllm \
  -n llm-serving --timeout=300s || true

kubectl rollout status deployment/llm-gateway \
  -n llm-serving --timeout=120s || true

echo ""
echo "========================================"
echo "Deployment complete!"
echo "========================================"

echo ""
echo "Current pods:"
kubectl get pods -n llm-serving

echo ""
echo "Current services:"
kubectl get svc -n llm-serving
