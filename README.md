# Ava Chief of Staff

A working prototype for a GPU-accelerated voice and chat assistant backed by persistent Pi coding-agent sessions. Users can speak or type in the browser, while Ava delegates substantive requests to a private chief-of-staff agent that can inspect a sandboxed workspace and delegate bounded work to ephemeral Pi workers.

Based on NVIDIA's open source [Nemotron Voice Agent](https://github.com/NVIDIA-AI-Blueprints/nemotron-voice-agent) blueprint and Pipecat.

## Stack

- OpenRouter `google/gemini-3.7-flash` for the voice Talker
- Pi SDK chief and worker sessions using Codex-plan `openai-codex/gpt-5.6-sol`
- Faster Whisper Large V3 Turbo on an NVIDIA GPU
- Kokoro ONNX TTS with CUDA Execution Provider
- Pipecat with WebRTC and WebSocket transports
- React browser UI with voice and typed input
- Sandboxed `/workspace` mount with read-only Pi tools by default

## Requirements

- Linux x86-64 with an NVIDIA CUDA GPU
- Docker Engine, Docker Compose, and NVIDIA Container Toolkit
- OpenRouter API key for the voice Talker
- ChatGPT Plus or Pro with Pi logged into the OpenAI Codex provider

The current GPU speech configuration was verified on an RTX 3090 with 24 GB VRAM.

## Quick Start

```bash
cp .env.example .env
```

Add your Talker key to `.env`:

```dotenv
OPENROUTER_API_KEY=your-key
```

Log into the ChatGPT Codex plan with host Pi using `/login`, then securely copy that OAuth credential into the private Pi data volume:

```bash
pi
# In Pi: /login → ChatGPT Plus/Pro (Codex)
docker compose --profile setup run --rm pi-auth-init
```

The copied credential is stored with mode `0600` in `PI_AGENT_DATA_VOLUME`, where Pi can refresh it without exposing it to `voice-agent`.

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

In `docker compose ps -a`, `model-init` should show `Exited (0)`; this is the expected successful state for the one-shot initializer. The `voice-agent` and `pi-agent` services should show `healthy`.

Open `https://localhost:7860/`, accept the development certificate, and connect. Replace `localhost` with the server IP for remote access. The first connection loads the cached speech models into GPU memory, but does not download them again.

```bash
# Follow logs
docker compose logs -f voice-agent pi-agent

# Stop without deleting model caches or agent state
docker compose down
```

## Runtime Flow

- Greetings and brief acknowledgements can be answered by Ava's fast Talker.
- Substantive questions and tasks are sent to the persistent chief Pi session.
- The chief can inspect the mounted workspace with its enabled tools.
- The chief can call `delegate_task` to run bounded work in an ephemeral Pi worker.
- The chief's final response returns through Kokoro TTS and the browser transcript.

Verify the active GPU speech path and Pi request audit trail in the logs:

```bash
docker compose logs --tail 200 voice-agent | grep -E \
  'Loaded Whisper model|device=cuda|execution_provider=CUDAExecutionProvider|Client connected'

docker compose logs --tail 200 voice-agent pi-agent | grep -E \
  'Pi request (started|completed)|"event":"request_(received|completed)"'
```

The same `request_id` appears in both services, proving that the voice gateway sent the request to Pi and received its completion.

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
| Ava voice facade | `src/examples/frontend_backend_agent/prompts.yaml` |
| Pi chief and worker service | `pi-agent-service/src/server.mjs` |
| Pi Codex provider and model defaults | `.env` and `docker-compose.yml` |
| Models, voices, and speech settings | `src/examples/frontend_backend_agent/services.local.yaml` |
| Browser interface | `client/src/` |
| Deployment and workspace isolation | `docker-compose.yml` and `.env` |
| AI coding-agent guidance | `AGENTS.md` and `skills/` |

Refer to [Configuration](docs/CONFIGURATION.md), [Troubleshooting](docs/TROUBLESHOOTING.md), and [Contributing](CONTRIBUTING.md).

## Upstream and Legacy Archive

This Pi-only branch derives from NVIDIA's [Nemotron Voice Agent](https://github.com/NVIDIA-AI-Blueprints/nemotron-voice-agent). The retired airline and booking demonstration is preserved outside the active tree at tag [`airline-demo-final`](https://github.com/netixc/g-force-voice-agent/tree/airline-demo-final) and branch [`archive/airline-demo`](https://github.com/netixc/g-force-voice-agent/tree/archive/airline-demo), both rooted at commit [`e922735b4d74018946619f8463dedbd6f219860e`](https://github.com/netixc/g-force-voice-agent/commit/e922735b4d74018946619f8463dedbd6f219860e). Do not restore that functionality to active branches without an explicit scope change.

Inspect the archive without changing this checkout:

```bash
git ls-tree -r airline-demo-final -- src/examples/frontend_backend_agent/airline/
```

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
