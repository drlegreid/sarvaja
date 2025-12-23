FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app
COPY pyproject.toml ./
RUN uv pip install --system -e .

COPY *.py ./

COPY <<EOF entrypoint.sh
#!/bin/sh
echo "=== Sim.ai PoC Agent ==="
echo "LiteLLM: \${LITELLM_BASE_URL}"
echo "Opik: \${OPIK_BASE_URL}"
echo "ChromaDB: \${CHROMADB_HOST}:\${CHROMADB_PORT}"
exec python playground.py
EOF

RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
