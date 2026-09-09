import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
    vus: 1,
    iterations: 5,
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8080";

export default function () {
    const payload = JSON.stringify({
        model: "Qwen/Qwen2.5-0.5B-Instruct",
        messages: [
            {
                role: "user",
                content: "Explain Kubernetes in one short sentence."
            }
        ],
        max_tokens: 50,
        temperature: 0.7
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
        "response has choices": (r) => {
            try {
                return JSON.parse(r.body).choices !== undefined;
            } catch {
                return false;
            }
        },
    });

    sleep(1);
}