FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS production
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
RUN mkdir -p uploads && chown -R appuser:appuser /app
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser ./app ./app
COPY --chown=appuser:appuser ./geoip ./geoip
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser alembic/ ./alembic/
USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c \
  "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["gunicorn", "app.main:app", \
     "-w", "1", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000"]