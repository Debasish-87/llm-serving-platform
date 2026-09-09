import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
    stages: [
        { duration: "30s", target: 2 },
        { duration: "1m", target: 5 },
        { duration: "2m", target: 10 },
        { duration: "30s", target: 0 },
    ],

    thresholds: {
        http_req_failed: ["rate<0.05"],
        http_req_duration: ["p(95)<30000"],
    },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8080";

export default function () {
    const payload = JSON.stringify({
        model: "Qwen/Qwen2.5-0.5B-Instruct",

        messages: [
            {
                role: "user",
                content:
                    "Explain how Kubernetes and vLLM work together for GPU-based LLM inference.",
            },
        ],

        max_tokens: 100,
        temperature: 0.7,
    });

    const params = {
        headers: {
            "Content-Type": "application/json",
        },

        timeout: "60s",
    };

    const response = http.post(
        `${BASE_URL}/v1/chat/completions`,
        payload,
        params
    );

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