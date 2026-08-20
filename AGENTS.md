# G Force Voice Agent Repository Guidance

## Scope

This repository contains one Frontend/Backend flight-booking voice agent. Preserve microphone and typed input, OpenRouter Talker and Thinker roles, GPU Faster Whisper, GPU Kokoro, and the booking-server workflow.

## Sources of Truth

- `pyproject.toml` and `uv.lock`: Python dependencies.
- `client/package.json` and `client/package-lock.json`: browser dependencies.
- `examples_registry.yaml`: exposed agent and transport defaults.
- `src/examples/frontend_backend_agent/`: prompts, service catalog, and behavior.
- `docker-compose.yml` and `docker/Dockerfile`: deployment and GPU runtime.
- `README.md` and `docs/`: user-facing behavior.

## Rules

- Run commands from the repository root.
- Preserve `.env`; never commit credentials.
- Keep `OPENROUTER_API_KEY` separate from public configuration.
- Keep `google/gemini-3.7-flash` without the OpenRouter `:batch` suffix.
- Keep Faster Whisper on CUDA and Kokoro on `CUDAExecutionProvider` unless the user explicitly requests a CPU fallback.
- Preserve license headers, `LICENSE`, and `third_party_oss_license.txt`.
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
docker compose config
```

Report checks that require unavailable credentials or GPU hardware rather than claiming they passed.
