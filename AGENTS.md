# Chief OS Repository Guidance

## Product Scope

This repository contains one working Ava Chief-of-Staff voice-agent prototype derived from NVIDIA Nemotron Voice Agent. Ava is the Chief of Staff and primary user interface; Pi agents are execution workers, not the chief. Preserve microphone and typed input, the OpenRouter Talker, persistent primary Pi sessions, delegated Pi workers, GPU Faster Whisper, and GPU Kokoro.

The product direction adds Ava-owned tools, visible task progress, direct Pi conversations, and explicit per-task context and file handoff. The current prototype still delegates substantive requests through Ava to Pi and mounts one configured workspace, so documentation must distinguish implemented behavior from planned behavior.

The active repository is Pi-only. Legacy airline demonstration source may be
removed from active branches after it is preserved in an archival branch or
tag. Document the archival reference and NVIDIA upstream repository instead of
retaining the airline implementation in the active tree. Do not restore or
expose booking functionality unless explicitly requested.

## Sources of Truth

- `pyproject.toml` and `uv.lock`: Python versions and dependencies.
- `client/package.json` and `client/package-lock.json`: browser dependencies and scripts.
- `examples_registry.yaml`: exposed agent, transports, and defaults.
- `src/examples/frontend_backend_agent/pipeline.py`: voice pipeline construction.
- `src/examples/frontend_backend_agent/prompts.yaml`: Ava Talker behavior.
- `src/examples/frontend_backend_agent/services.local.yaml`: Talker and speech services.
- `pi-agent-service/src/server.mjs`: Primary Pi agent, workers, sessions, and audit events.
- `docker-compose.yml` and `docker/Dockerfile`: deployment, OAuth import, and GPU runtime.
- `README.md` and `docs/`: user-facing behavior.

## Repository Rules

- Run commands from the repository root.
- Preserve `.env`; never commit credentials.
- Keep `.env`, Docker overrides, OAuth files, model caches, databases, and generated files ignored.
- Keep the Talker on `google/gemini-3.7-flash` without the OpenRouter `:batch` suffix.
- Keep the primary Pi agent and workers on the configured built-in `openai-codex/gpt-5.6-sol` model unless explicitly requested otherwise.
- Never copy OAuth values into source files or command output. `pi-auth-init` may copy only the `openai-codex` entry into the private Pi data volume.
- Keep Faster Whisper on CUDA and Kokoro on `CUDAExecutionProvider` unless a CPU fallback is requested.
- Keep Pi workspace access read-only by default.
- Preserve license headers, `LICENSE`, NVIDIA attribution, and `third_party_oss_license.txt`.
- Keep active branches focused on the Pi backend. Airline and booking source
 may remain only in archival Git references.

## Workflows

- Read `skills/configure-agent/SKILL.md` before changing prompts, model catalogs, speech settings, or `.env.example`.
- Read `skills/deploy/SKILL.md` before changing Compose, Docker, ports, volumes, OAuth import, CUDA libraries, or startup behavior.
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
npm --prefix pi-agent-service ci --ignore-scripts
npm --prefix pi-agent-service run check
docker compose config
```

For documentation changes, run:

```bash
uv run pre-commit run --files <changed-files>
git diff --check
```

Report checks that require unavailable subscription credentials, GPU hardware, or external services instead of claiming they passed.
