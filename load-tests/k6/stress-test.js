import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
    stages: [
        { duration: "30s", target: 5 },
        { duration: "1m", target: 10 },
        { duration: "1m", target: 15 },
        { duration: "1m", target: 20 },
        { duration: "1m", target: 0 },
    ],

    thresholds: {
        http_req_failed: ["rate<0.20"],
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
                    "Explain in detail how continuous batching improves LLM inference throughput in vLLM.",
            },
        ],

        max_tokens: 200,
        temperature: 0.7,
    });

    const params = {
        headers: {
            "Content-Type": "application/json",
        },

        timeout: "120s",
    };

    const response = http.post(
        `${BASE_URL}/v1/chat/completions`,
        payload,
        params
    );

    check(response, {
        "status is successful": (r) => r.status === 200,

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