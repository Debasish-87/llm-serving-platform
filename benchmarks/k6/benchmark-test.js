import http from "k6/http";
import { check, sleep } from "k6";

// Builds ramping-vus stages from CONCURRENCY_STEPS (e.g. "1,2,4,8") so the
// saturation point shows up as a bend in the latency curve rather than
// being guessed at from a single fixed load level.
const steps = (__ENV.CONCURRENCY_STEPS || "1,2,4,8")
    .split(",")
    .map((s) => parseInt(s.trim(), 10));

const stepDuration = __ENV.STEP_DURATION || "60s";

const stages = [];
for (const target of steps) {
    stages.push({ duration: stepDuration, target });
}
// Ramp down cleanly at the end.
stages.push({ duration: "15s", target: 0 });

export const options = {
    stages,
    thresholds: {
        http_req_failed: ["rate<0.05"],
    },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8080";
const MODEL = __ENV.MODEL || "Qwen/Qwen2.5-0.5B-Instruct";

export default function () {
    const payload = JSON.stringify({
        model: MODEL,
        messages: [
            {
                role: "user",
                content:
                    "Explain how Kubernetes and vLLM work together for GPU-based LLM inference.",
            },
        ],
        // Fixed max_tokens keeps the tokens/sec approximation in
        // build_result.py consistent across configs and runs.
        max_tokens: 100,
        temperature: 0.7,
    });

    const params = {
        headers: { "Content-Type": "application/json" },
        timeout: "60s",
    };

    const response = http.post(`${BASE_URL}/v1/chat/completions`, payload, params);

    check(response, {
        "status is 200": (r) => r.status === 200,
        "response contains choices": (r) => {
            try {
                const body = JSON.parse(r.body);
                return body.choices && body.choices.length > 0;
            } catch {
                return false;
            }
        },
    });

    sleep(1);
}
