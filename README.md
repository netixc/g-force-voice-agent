# Chief OS

A working prototype for a GPU-accelerated voice and chat Chief of Staff backed by persistent Pi coding-agent sessions. Users speak or type to Ava, the Chief of Staff. Ava delegates substantive work to a primary Pi execution agent, which can inspect a sandboxed workspace and delegate bounded work to ephemeral Pi workers.

Based on NVIDIA's open source [Nemotron Voice Agent](https://github.com/NVIDIA-AI-Blueprints/nemotron-voice-agent) blueprint and Pipecat.

## Stack

- OpenRouter `google/gemini-3.7-flash` for the voice Talker
- Pi SDK primary-agent and worker sessions using Codex-plan `openai-codex/gpt-5.6-sol`
- Faster Whisper Large V3 Turbo on an NVIDIA GPU
- Kokoro ONNX TTS with CUDA Execution Provider
- Pipecat with WebRTC and WebSocket transports
- React browser UI with voice and typed input
- Workspace-confined Pi filesystem tools, read-only by default

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

- Ava is the user's Chief of Staff and the primary voice-and-text interface.
- Greetings and brief acknowledgements can be answered by Ava's fast Talker.
- Ava currently uses delegation and cancellation tools; substantive requests go to a persistent primary Pi session.
- Primary session files survive service restarts in `PI_AGENT_DATA_VOLUME`; idle sessions are released from memory and restored on demand.
- The primary Pi agent can inspect only the mounted workspace through workspace-confined filesystem tools.
- The primary Pi agent can call `delegate_task` to run bounded work in an ephemeral Pi worker.
- Sanitized request, agent, tool, and worker progress is available from the internal session event stream.
- Pi's final response returns through Ava, Kokoro TTS, and the browser transcript.

## Product Direction

The target experience keeps one main conversation with Ava while adding direct Chief-of-Staff tools, visible task and worker progress, and an option to open a direct chat with a Pi agent. Direct Pi tasks should receive only the task context and files Ava or the user explicitly provides. The local deployment remains the first target; a future hosted mode must keep speech recognition and synthesis on the user's local GPU. Any future purchasing capability must require explicit user approval.

The current prototype does not yet provide the progress panel, direct Pi chat, per-task file handoff, or purchase approval UI. Its Pi service can access the configured `workspace/` mount, subject to the enabled tools.

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
PI_AGENT_TOOLS=read,grep,find,ls
```

Add `edit` and `write` only when Pi should modify workspace files:

```dotenv
PI_AGENT_TOOLS=read,grep,find,ls,edit,write
```

`bash` is intentionally rejected until terminal execution runs in a separate sandbox without access to Pi OAuth credentials. Pi runs as a non-root user, receives only `./workspace` as task data, and does not receive the Docker socket. Its filesystem tools reject paths and symlinks that escape the workspace. Do not put `.env`, SSH keys, production credentials, customer data, or other secrets in `workspace/`.

## Customize

| Area | Path |
| --- | --- |
| Ava Chief-of-Staff behavior | `src/examples/frontend_backend_agent/prompts.yaml` |
| Primary Pi agent and worker service | `pi-agent-service/src/server.mjs` |
| Pi Codex provider and model defaults | `.env` and `docker-compose.yml` |
| Models, voices, and speech settings | `src/examples/frontend_backend_agent/services.local.yaml` |
| Browser interface | `client/src/` |
| Deployment and workspace isolation | `docker-compose.yml` and `.env` |
| AI coding-agent guidance | `AGENTS.md` and `skills/` |

Refer to [Product Direction](docs/PRODUCT_DIRECTION.md), [Configuration](docs/CONFIGURATION.md), [Troubleshooting](docs/TROUBLESHOOTING.md), and [Contributing](CONTRIBUTING.md).

## Upstream and Legacy Archive

This Pi-focused repository derives from NVIDIA's [Nemotron Voice Agent](https://github.com/NVIDIA-AI-Blueprints/nemotron-voice-agent). The retired airline and booking demonstration is preserved outside the active tree at tag [`airline-demo-final`](https://github.com/netixc/chief-os/tree/airline-demo-final) and branch [`archive/airline-demo`](https://github.com/netixc/chief-os/tree/archive/airline-demo), both rooted at commit [`e922735b4d74018946619f8463dedbd6f219860e`](https://github.com/netixc/chief-os/commit/e922735b4d74018946619f8463dedbd6f219860e). Do not restore that functionality to active branches without an explicit scope change.

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
