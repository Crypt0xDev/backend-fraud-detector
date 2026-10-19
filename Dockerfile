FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app

COPY requirements.txt .
RUN sed -e 's/^xgboost==/xgboost-cpu==/' \
        -e '/^ruff==/d' \
        requirements.txt > /tmp/requirements.txt \
    && pip install --no-cache-dir -r /tmp/requirements.txt
RUN useradd --create-home --uid 1000 app

COPY --chown=app . .
RUN mkdir -p /app/storage && chown app /app/storage

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["sh", "-c", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/api/v1/health', timeout=4)\""]

CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
