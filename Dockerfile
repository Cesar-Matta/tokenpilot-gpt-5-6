# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

WORKDIR /build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
COPY pyproject.toml README.md ./
COPY app ./app
RUN python -m pip install --upgrade pip && pip wheel --wheel-dir /wheels .

FROM python:3.12-slim AS runtime

ARG APP_UID=10001
ARG APP_GID=10001
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN groupadd --gid ${APP_GID} tokenpilot \
    && useradd --uid ${APP_UID} --gid ${APP_GID} --create-home --shell /usr/sbin/nologin tokenpilot
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY --chown=tokenpilot:tokenpilot app ./app
COPY --chown=tokenpilot:tokenpilot config ./config
USER tokenpilot
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health/live', timeout=2)" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]
