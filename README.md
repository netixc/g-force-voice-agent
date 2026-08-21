# Ava Chief of Staff

A working prototype for a GPU-accelerated voice and chat assistant backed by persistent Pi coding-agent sessions. Users can speak or type in the browser, while Ava delegates substantive requests to a private chief-of-staff agent that can inspect a sandboxed workspace and delegate bounded work to ephemeral Pi workers.

Based on NVIDIA's open source [Nemotron Voice Agent](https://github.com/NVIDIA-AI-Blueprints/nemotron-voice-agent) blueprint and Pipecat. The preserved airline workflow remains available as a demonstration mode.

## Stack

- OpenRouter `google/gemini-3.7-flash` for the voice Talker and Pi agents
- Pi SDK chief-of-staff session with delegated worker sessions
- Faster Whisper Large V3 Turbo on an NVIDIA GPU
- Kokoro ONNX TTS with CUDA Execution Provider
- Pipecat with WebRTC and WebSocket transports
- React browser UI with voice and typed input
- Sandboxed `/workspace` mount with read-only Pi tools by default

## Requirements

- Linux x86-64 with an NVIDIA CUDA GPU
- Docker Engine, Docker Compose, and NVIDIA Container Toolkit
- OpenRouter API key

The current GPU speech configuration was verified on an RTX 3090 with 24 GB VRAM.

## Quick Start

```bash
cp .env.example .env
```

Add your key to `.env`:

```dotenv
OPENROUTER_API_KEY=your-key
```

Create the sandboxed workspace. The default Pi configuration can read it but cannot modify it:

```bash
mkdir -p workspace
```

Build and run. On the first start, `model-init` downloads Faster Whisper and Kokoro into the persistent model cache and validates both with GPU providers before the voice server starts:

```bash
docker compose up -d --build
docker compose logs -f model-init
docker compose ps
```

Open `https://localhost:7860/`, accept the development certificate, and connect. Replace `localhost` with the server IP for remote access.

```bash
# Follow logs
docker compose logs -f voice-agent pi-agent

# Stop without deleting model caches or agent state
docker compose down
```

## Pi Permissions

The default tool set is read-only:

```dotenv
CHIEF_PI_TOOLS=read,grep,find,ls
```

Only add `edit`, `write`, or `bash` after reviewing the security implications:

```dotenv
CHIEF_PI_TOOLS=read,grep,find,ls,edit,write,bash
```

Pi runs as a non-root user, receives only `./workspace`, and does not receive the Docker socket. Do not put `.env`, SSH keys, production credentials, customer data, or other secrets in `workspace/`.

## Customize

| Area | Path |
| --- | --- |
| Ava voice facade and preserved airline prompts | `src/examples/frontend_backend_agent/prompts.yaml` |
| Pi chief and worker service | `pi-agent-service/src/server.mjs` |
| Pi custom OpenRouter model | `pi-agent-service/models.json` |
| Models, voices, and speech settings | `src/examples/frontend_backend_agent/services.local.yaml` |
| Browser interface | `client/src/` |
| Deployment and workspace isolation | `docker-compose.yml` and `.env` |
| Preserved airline workflow | `src/examples/frontend_backend_agent/airline/` |
| AI coding-agent guidance | `AGENTS.md` and `skills/` |

Refer to [Configuration](docs/CONFIGURATION.md), [Troubleshooting](docs/TROUBLESHOOTING.md), and [Contributing](CONTRIBUTING.md).

## Preserved Airline Mode

Set `AGENT_BACKEND=airline` and select the `talker` prompt to use the original demonstration booking workflow. Its local database contains demonstration data only and is not connected to a real airline or customer system.

## Prototype Status

This is a working prototype intended for personal development and further security work. Before exposing it to other users, add authentication, trusted TLS, per-user workspace isolation, approval controls, monitoring, and explicit retention policies.

## Development

```bash
uv sync --dev
uv run pytest tests/ -v
uv run ruff check .
npm --prefix client ci
npm --prefix client run lint
npm --prefix client run build
npm --prefix pi-agent-service ci --ignore-scripts
npm --prefix pi-agent-service run check
```

## Security and License

`.env`, local Compose overrides, workspaces, model files, and databases are ignored by Git. Never commit credentials or customer data.

The project retains the upstream BSD-2-Clause [`LICENSE`](LICENSE), NVIDIA copyright headers, and [`third_party_oss_license.txt`](third_party_oss_license.txt).
