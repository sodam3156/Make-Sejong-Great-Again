FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    RAINFLOW_HOST=0.0.0.0 \
    RAINFLOW_PORT=8000

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --requirement requirements.txt \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin rainflow

COPY --chown=rainflow:rainflow backend ./backend
COPY --chown=rainflow:rainflow contracts ./contracts
COPY --chown=rainflow:rainflow frontend ./frontend
COPY --chown=rainflow:rainflow launcher ./launcher

RUN mkdir -p /app/backend/logs \
    && chown rainflow:rainflow /app/backend/logs

USER rainflow

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=2s --start-period=10s --retries=6 \
    CMD ["python", "-c", "import json, os, urllib.request; port = os.environ.get('RAINFLOW_PORT', '8000'); response = urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health', timeout=1); data = json.load(response); raise SystemExit(0 if response.status == 200 and data.get('status') == 'ok' else 1)"]

CMD ["python", "-m", "launcher.run_rainflow"]
