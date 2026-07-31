# TokenPilot GPT-5.6

> **Open-source smart model router for OpenAI GPT-5.6 Luna, Terra, and Sol—automatically balance cost, quality, risk, and latency.**

[![CI](https://github.com/REPLACE_WITH_OWNER/tokenpilot-gpt-5-6/actions/workflows/ci.yml/badge.svg)](https://github.com/REPLACE_WITH_OWNER/tokenpilot-gpt-5-6/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![OpenAPI](https://img.shields.io/badge/API-OpenAPI-6BA539.svg)](docs/api.md)

## Choose what you want to install

TokenPilot contains two separate products. You can install either one without installing the other.

| Product | What it does | Requirements | OpenAI API key |
|---|---|---|---:|
| **TokenPilot Skill** | Gives Codex an explainable workflow for recommending Luna, Terra, or Sol | Copy one folder | **Not required** |
| **TokenPilot Server** | Routes and executes real API requests automatically | Python or Docker | **Required only for execution** |

They are physically separated:

```text
skills/tokenpilot-router/   # standalone skill: copy only this folder
app/                        # optional FastAPI server
config/                     # optional server policy and pricing
Dockerfile                  # optional server deployment
```

### I only want the Codex skill

Install only [`skills/tokenpilot-router`](skills/tokenpilot-router). Do **not** install Python dependencies, create an `.env` file, start Docker, or configure `OPENAI_API_KEY`.

Read the [standalone Codex installation guide](docs/install-skill.md). After installation, invoke:

```text
$tokenpilot-router
```

> [!IMPORTANT]
> The standalone skill provides routing guidance inside Codex. It does not call the OpenAI API and cannot silently change the model powering the current Codex conversation. The optional server performs actual automatic routing for applications and workflows.

### I want automatic API routing

Install the server described in [Server quick start](#server-quick-start). It is a production-oriented **OpenAI model router**, **LLM router**, and **token cost optimization** service. It sends routine API work to **GPT-5.6 Luna**, escalates nuanced work to **GPT-5.6 Terra**, and reserves **GPT-5.6 Sol** for difficult or high-risk requests.

It is independent software and is not affiliated with, endorsed by, or sponsored by OpenAI.

## Why the server?

- Default to the economical model without hiding the decision.
- Use complexity, risk, confidence, context size, task type, and domain as routing signals.
- Enforce conservative minimums for legal, medical, financial, safety, and security workloads.
- Return a human-readable decision, escalation path, and cost estimate before execution.
- Proxy the OpenAI Responses API with API-key protection, rate limiting, structured errors, Prometheus metrics, and request IDs.
- Integrate through ordinary HTTP from any workflow engine, application, or service.

## Model policy

| Tier | OpenAI model | Default use |
|---|---|---|
| Luna | `gpt-5.6-luna` | High-volume extraction, classification, summaries, and routine generation |
| Terra | `gpt-5.6-terra` | Technical work, nuanced questions, uncertainty, and larger context |
| Sol | `gpt-5.6-sol` | Critical, high-risk, or difficult reasoning workloads |

The versioned catalog uses OpenAI's published standard pricing from **2026-07-30**, including short- and long-context rates, cached input, cache writes, and output. Regional processing, non-standard service tiers, and tool fees are intentionally excluded. Review [`config/models.yaml`](config/models.yaml) before relying on estimates in a live environment. See the [official pricing page](https://developers.openai.com/api/docs/pricing).

## Server quick start

```bash
git clone https://github.com/REPLACE_WITH_OWNER/tokenpilot-gpt-5-6.git
cd tokenpilot-gpt-5-6
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\Activate.ps1
python -m pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload --port 8080
```

Open [http://localhost:8080/docs](http://localhost:8080/docs) for the generated OpenAPI documentation.

### Ask for a route without calling OpenAI

```bash
curl -X POST http://localhost:8080/v1/route \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Extract the order number and due date.",
    "signals": {"task_type": "extraction", "domain": "general"},
    "max_cost_usd": 0.01
  }'
```

### Execute through the Responses API

Set `OPENAI_API_KEY` in `.env`, then call:

```bash
curl -X POST http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Summarize this support ticket in three bullets.",
    "signals": {"task_type": "summarization"}
  }'
```

## API

| Endpoint | Purpose |
|---|---|
| `POST /v1/route` | Explain the selected model without provider spend |
| `POST /v1/responses` | Route and execute an OpenAI Responses API request |
| `POST /v1/estimate` | Estimate a model request from token counts |
| `GET /v1/models` | Read the versioned model and pricing catalog |
| `GET /health/live` | Liveness probe |
| `GET /health/ready` | Readiness probe |
| `GET /metrics` | Prometheus metrics |

Read the full [API reference](docs/api.md), [routing policy](docs/policies.md), [architecture](docs/architecture.md), [cost guide](docs/costs.md), [evaluation guide](docs/evaluation.md), and [deployment guide](docs/deployment.md).

## Docker

```bash
cp .env.example .env
# Set OPENAI_API_KEY and production API-key settings in .env first.
docker compose up --build
```

The container is non-root, read-only at runtime, capability-reduced, health-checked, and exposes only port 8080.

## Integrations

- [Generic workflow-automation example](docs/n8n.md)
- [Python example](examples/python_client.py)
- [Portable workflow JSON](examples/tokenpilot-workflow.json)

## Standalone skill

The complete skill lives only in [`skills/tokenpilot-router`](skills/tokenpilot-router). That directory is self-contained and can be copied independently. See [Install only the TokenPilot skill](docs/install-skill.md).

## Public release checklist

Run before publishing:

```bash
python scripts/public_release_check.py
python scripts/run_routing_evals.py
pytest
ruff check .
ruff format --check .
```

The checker detects likely credentials, local paths, and disallowed private references. See [the public-release guide](docs/public-release.md).

## SEO and discovery

Use the GitHub repository description and topics in [`docs/seo.md`](docs/seo.md). The README deliberately includes natural search terms such as **OpenAI GPT-5.6 router**, **Luna Terra Sol**, **LLM routing**, **token saver**, **AI gateway**, and **cost optimization** without keyword stuffing.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). TokenPilot is released under [Apache-2.0](LICENSE).
