# Contributing

This repository is a working prototype intended for iterative development.

## Setup

```bash
cp .env.example .env
uv sync --dev
npm --prefix client ci
```

Keep API keys and local deployment overrides out of Git.

## Before a Change

- Read `AGENTS.md` for repository guidance.
- Read the relevant workflow in `skills/`.
- Keep changes focused and preserve NVIDIA attribution and license notices.
- Update documentation when behavior or configuration changes.

## Validation

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest tests/ -v
npm --prefix client run lint
npm --prefix client run build
docker compose config
```

GPU, OpenRouter, and browser behavior must also be tested on a suitable deployment when those surfaces change.

## Pull Requests

Describe the user impact, configuration changes, tests run, documentation updates, and any validation blocked by unavailable hardware or credentials.
