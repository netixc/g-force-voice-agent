# Contributing

This repository is a working prototype intended for iterative development.

## Setup

```bash
cp .env.example .env
uv sync --dev
npm --prefix client ci
npm --prefix pi-agent-service ci --ignore-scripts
```

For live deployment, authenticate host Pi with ChatGPT Plus/Pro (Codex), then run `docker compose --profile setup run --rm pi-auth-init`. Keep API keys, OAuth credentials, and local deployment overrides out of Git.

## Before a Change

- Read `AGENTS.md` for repository guidance.
- Read the relevant workflow in `skills/`.
- Keep changes focused and preserve NVIDIA attribution and license notices.
- Update documentation when behavior or configuration changes.

## Validation

```bash
uvx ruff@0.15.6 check .
uvx ruff@0.15.6 format --check .
uv sync --dev
uv run pytest tests/ -v
npm --prefix client ci
npm --prefix client run lint
npm --prefix client run build
npm --prefix pi-agent-service ci --ignore-scripts
npm --prefix pi-agent-service run check
docker compose config
```

GPU, OpenRouter Talker, OpenAI Codex Pi, and browser behavior must also be tested on a suitable deployment when those surfaces change.

## Pull Requests

Describe the user impact, configuration changes, tests run, documentation updates, and any validation blocked by unavailable hardware or credentials.
