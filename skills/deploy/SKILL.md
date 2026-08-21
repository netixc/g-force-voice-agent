---
name: deploy
description: Build, start, stop, and troubleshoot the standalone GPU voice-agent deployment.
version: "1.0.0"
---

# Deploy

## Prerequisites

- Docker Engine and Docker Compose
- NVIDIA Container Toolkit
- NVIDIA GPU visible to Docker
- Private `.env` with `OPENROUTER_API_KEY` for the Talker
- Host Pi authenticated to ChatGPT Plus/Pro (Codex)

## Start

```bash
docker compose config
docker compose --profile setup run --rm pi-auth-init
docker compose up -d --build
docker compose ps
```

The expected long-running services are `voice-agent` and `pi-agent`. The one-shot `model-init` service must complete successfully before `voice-agent` starts. The browser endpoint is `https://<host>:7860/` by default.

## Verify GPU Runtime

```bash
docker compose exec voice-agent nvidia-smi
docker compose exec voice-agent uv run python -c \
  'import onnxruntime as o; print(o.get_available_providers())'
```

The ONNX provider list must include `CUDAExecutionProvider`. Start a browser session before checking model VRAM because speech models load per session.

## Logs

```bash
docker compose logs -f model-init voice-agent pi-agent
```

## Stop

```bash
docker compose down
```

Do not add `-v` unless model caches and Pi agent state should be deleted.

## Rules

- Preserve named volumes when recreating containers.
- Avoid exposing `.env` in logs or diagnostics.
- Do not run another stack on port `7860` simultaneously.
- Keep HTTPS enabled for browser microphone and WebRTC use.
- Document changes to ports, volumes, device selection, or startup commands.
