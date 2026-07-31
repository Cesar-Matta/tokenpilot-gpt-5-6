# Deployment guide

## Before deployment

1. Update [`config/models.yaml`](../config/models.yaml) from the current official pricing source.
2. Set `ENVIRONMENT=production`.
3. Set `REQUIRE_API_KEY=true` and a random `TOKENPILOT_API_KEYS` value in your secret manager.
4. Set `OPENAI_API_KEY` only in the runtime secret manager.
5. Restrict `ALLOWED_ORIGINS` to known browser clients, or leave it empty for server-to-server use.
6. Put the service behind TLS, an ingress proxy, or an API gateway.
7. Run a real health check, an authenticated `/v1/route` check, and a deliberately invalid-key check.

## Docker

```bash
docker build -t tokenpilot-gpt-5-6:0.1.0 .
docker run --rm -p 8080:8080 --env-file .env tokenpilot-gpt-5-6:0.1.0
```

The image uses a non-root user. Prefer a read-only root filesystem, no Linux capabilities, resource limits, and a platform-managed secret store.

## Cloud Run

TokenPilot is compatible with any container platform. For Cloud Run, replace the placeholders below with your own values:

```bash
gcloud builds submit --tag REGION-docker.pkg.dev/PROJECT/REPOSITORY/tokenpilot:0.1.0
gcloud run deploy tokenpilot \
  --image REGION-docker.pkg.dev/PROJECT/REPOSITORY/tokenpilot:0.1.0 \
  --region REGION \
  --port 8080 \
  --no-allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production,REQUIRE_API_KEY=true \
  --set-secrets OPENAI_API_KEY=openai-api-key:latest,TOKENPILOT_API_KEYS=tokenpilot-api-keys:latest
```

Set Cloud Run authentication, network ingress, and secret access according to your organization. Do not rely on a public unauthenticated endpoint merely because TokenPilot has API-key middleware.

## Observability

Scrape `/metrics` with Prometheus. Alert on rising `5xx` responses, elevated latency, unexpected Sol usage, route mix changes, and budget trend anomalies. TokenPilot emits JSON request-completion logs without prompts, provider payloads, or credential values.

## Scale-out note

The built-in limiter is per process. Deploy a gateway or shared limiter before using multiple replicas.
