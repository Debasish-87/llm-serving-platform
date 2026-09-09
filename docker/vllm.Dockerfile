FROM vllm/vllm-openai:latest

WORKDIR /app

EXPOSE 8000

ENTRYPOINT ["vllm", "serve"]
