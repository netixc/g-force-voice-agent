# Configuration

## Environment

The deployment reads `.env` through Docker Compose.

| Setting | Default | Purpose |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | Required | Authenticates the Talker and Pi agents. |
| `OPENROUTER_APP_NAME` | `G Force Voice Agent` | OpenRouter attribution title. |
| `AGENT_BACKEND` | `pi` | Selects `pi` chief-of-staff mode or preserved `airline` mode. |
| `CHIEF_PI_PROVIDER` | `openrouter` | Pi model provider. |
| `CHIEF_PI_MODEL` | `google/gemini-3.7-flash` | Pi chief and worker model. |
| `CHIEF_PI_THINKING_LEVEL` | `low` | Pi reasoning level. |
| `CHIEF_PI_TOOLS` | `read,grep,find,ls` | Tools enabled for chief and worker sessions. |
| `CHIEF_PI_MAX_WORKERS` | `2` | Maximum concurrent delegated Pi workers. |
| `PI_AGENT_TIMEOUT_SECONDS` | `300` | Voice gateway timeout for a chief request. |
| `PI_AGENT_DATA_VOLUME` | `g-force-voice-agent_pi_agent_data` | Pi catalog and agent runtime state. |
| `PIPELINE_APP_PORT` | `7860` | Browser application host port. |
| `BOOKING_SERVER_PORT` | `8001` | Preserved demonstration booking API host port. |
| `PIPELINE_TLS` | `true` | Enables the built-in self-signed HTTPS certificate. |
| `FASTER_WHISPER_DEVICE` | `cuda` | Faster Whisper inference device. |
| `FASTER_WHISPER_COMPUTE_TYPE` | `float16` | Faster Whisper CTranslate2 precision. |
| `FASTER_WHISPER_NO_SPEECH_PROB` | `0.4` | No-speech filtering threshold. |
| `ONNX_PROVIDER` | `CUDAExecutionProvider` | Kokoro ONNX execution provider. |
| `CHAT_HISTORY_RECENT_TURNS` | `20` | Number of recent messages retained in Talker context. |
| `MODEL_CACHE_VOLUME` | `g-force-voice-agent_model_cache` | Docker volume for downloaded speech models and package caches. |
| `BOOKING_DATA_VOLUME` | `g-force-voice-agent_booking_data` | Docker volume for demonstration SQLite booking state. |

Recreate services after changing `.env`:

```bash
docker compose up -d --force-recreate
```

## Pi Chief-of-Staff Service

The `pi-agent` service creates one in-memory chief `AgentSession` for each voice connection. The chief can call `delegate_task` to create a bounded ephemeral worker session. Chief sessions last until the service restarts; long-term personal memory is not implemented yet.

The service mounts only `./workspace` at `/workspace`. The container runs as the non-root `node` user, drops Linux capabilities, uses a read-only root filesystem, and does not receive the Docker socket.

The default tools are read-only:

```dotenv
CHIEF_PI_TOOLS=read,grep,find,ls
```

To permit file changes and commands inside the workspace, explicitly enable the additional tools:

```dotenv
CHIEF_PI_TOOLS=read,grep,find,ls,edit,write,bash
```

The current prototype does not provide a browser approval dialog. Enabling `bash`, `edit`, or `write` grants those tools for every request in that deployment. Keep the service private and never place credentials in `workspace/`.

## Language Models

The Talker model is configured in `src/examples/frontend_backend_agent/services.local.yaml`. The Pi model is configured in `pi-agent-service/models.json` because the installed Pi catalog does not currently include `google/gemini-3.7-flash`.

Both roles use interactive OpenRouter requests:

```text
google/gemini-3.7-flash
```

Do not add the `:batch` suffix. The Talker model must support OpenAI-compatible `tools` and `tool_choice`. The Pi model must support coding-agent tool calls.

## Prompts and Persona

Edit `src/examples/frontend_backend_agent/prompts.yaml`:

- `chief` controls Ava's voice facade and is the default.
- `talker` controls the preserved airline voice facade.
- `thinker` controls preserved airline planning.

The Pi chief and worker system prompts are in `pi-agent-service/src/server.mjs`.

Restart the affected services after editing prompts:

```bash
docker compose restart voice-agent pi-agent
```

## Preserved Airline Mode

The original demonstration booking workflow remains available:

```dotenv
AGENT_BACKEND=airline
```

Select the `talker` prompt in the browser when using this mode. The `booking-server` remains part of Compose to preserve flight search, new booking, and PNR demonstration behavior.

## Speech

Faster Whisper and Kokoro run in the voice-agent process on GPU 0. Docker exposes the device and provides the CUDA, cuDNN, cuBLAS, cuFFT, and cuRAND library paths.

Set `ONNX_PROVIDER=CPUExecutionProvider` only when you intentionally want Kokoro on the CPU. The pipeline rejects an unavailable requested provider instead of silently accepting a fallback.

## Welcome Message

The default registry disables the automatic greeting:

```yaml
welcome_message: false
```

Change it to `true`, then restart `voice-agent`, to restore the greeting.

## Ports and Parallel Deployments

Change the browser host port when another deployment uses `7860`:

```dotenv
PIPELINE_APP_PORT=7861
```

The Pi service is only exposed to the internal Compose network on port `8787`. `PI_AGENT_URL` is available for an explicitly configured external Pi service.
