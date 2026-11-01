FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
ENV FORWARDED_ALLOW_IPS=127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,fc00::/7
WORKDIR /app

COPY requirements.txt .
RUN sed -e 's/^xgboost==/xgboost-cpu==/' requirements.txt > /tmp/requirements.txt \
    && pip install --no-cache-dir -r /tmp/requirements.txt
RUN useradd --create-home --uid 1000 app

COPY --chown=app . .
RUN mkdir -p /app/storage && chown app /app/storage

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD ["sh", "-c", "python -c \"import json, urllib.request; health = json.load(urllib.request.urlopen('http://localhost:${PORT}/api/v1/health', timeout=9)); assert health['status'] == 'ok'\""]

CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --proxy-headers"]
