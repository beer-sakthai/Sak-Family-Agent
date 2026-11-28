FROM python:3.12-slim

# Create unprivileged system user
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -s /sbin/nologin -d /app appuser

WORKDIR /app

# Install dependencies
COPY pyproject.toml /app/
RUN pip install --no-cache-dir .

# Copy application source
COPY src/ /app/src/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "sak_mcp_gateway.gateway:app", "--host", "0.0.0.0", "--port", "8000"]
