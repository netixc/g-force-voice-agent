# G Force Voice Agent Repository Guidance

## Product Scope

This repository contains one working Frontend/Backend airline voice-agent prototype derived from NVIDIA Nemotron Voice Agent. Preserve microphone and typed input, OpenRouter Talker and Thinker roles, GPU Faster Whisper, GPU Kokoro, and the booking-server workflow.

Treat the included airline system as demonstration code. Do not describe it as production-ready or connect it to real customer data without explicit security and integration work.

## Sources of Truth

- `pyproject.toml` and `uv.lock`: Python versions and dependencies.
- `client/package.json` and `client/package-lock.json`: browser dependencies and scripts.
- `examples_registry.yaml`: exposed agent, transports, and defaults.
- `src/examples/frontend_backend_agent/pipeline.py`: pipeline construction.
- `src/examples/frontend_backend_agent/prompts.yaml`: Talker and Thinker behavior.
- `src/examples/frontend_backend_agent/services.local.yaml`: models and speech services.
- `src/examples/frontend_backend_agent/airline/`: booking workflow and demonstration data.
- `docker-compose.yml` and `docker/Dockerfile`: deployment and GPU runtime.
- `README.md` and `docs/`: user-facing behavior.

## Repository Rules

- Run commands from the repository root.
- Preserve `.env`; never commit credentials.
- Keep `.env`, `docker-compose.override.yml`, model caches, databases, and generated files ignored.
- Keep `google/gemini-3.7-flash` without the OpenRouter `:batch` suffix.
- Keep Faster Whisper on CUDA and Kokoro on `CUDAExecutionProvider` unless a CPU fallback is requested.
- Preserve license headers, `LICENSE`, NVIDIA attribution, and `third_party_oss_license.txt`.
- Do not infer production credentials, booking-system access, or deployment hardware.

## Workflows

- Read `skills/configure-agent/SKILL.md` before changing prompts, model catalogs, speech settings, or `.env.example`.
- Read `skills/deploy/SKILL.md` before changing Compose, Docker, ports, volumes, CUDA libraries, or startup behavior.
- Update documentation for user-visible changes. Follow `docs/AGENTS.md`.
- Preserve unrelated keys and comments when editing configuration.

## Validation

Run checks that match the changed surface:

```bash
uvx ruff@0.15.6 check .
uvx ruff@0.15.6 format --check .
uv sync --dev
uv run pytest tests/ -v
npm --prefix client ci
npm --prefix client run lint
npm --prefix client run build
docker compose config
```

For documentation changes, run:

```bash
uv run pre-commit run --files <changed-files>
git diff --check
```

Report checks that require unavailable API credentials, GPU hardware, or external services instead of claiming they passed.
