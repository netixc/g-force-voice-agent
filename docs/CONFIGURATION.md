# Configuration

## Environment

The deployment reads `.env` through Docker Compose.

| Setting | Default | Purpose |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | Required | Authenticates the voice Talker only. |
| `OPENROUTER_APP_NAME` | `Chief OS` | OpenRouter attribution title. |
| `OPENROUTER_HTTP_REFERER` | Empty | Optional OpenRouter attribution URL. |
| `PI_AGENT_PROVIDER` | `openai-codex` | Pi subscription provider. |
| `PI_AGENT_MODEL` | `gpt-5.6-sol` | Primary Pi agent and worker model. |
| `PI_AGENT_THINKING_LEVEL` | `low` | Pi reasoning level. |
| `PI_AGENT_TOOLS` | `read,grep,find,ls` | Tools enabled for primary and worker sessions. |
| `PI_AGENT_MAX_WORKERS` | `2` | Maximum concurrent delegated Pi workers. |
| `PI_AGENT_TIMEOUT_SECONDS` | `300` | Voice gateway timeout for a delegated request. |
| `PI_AGENT_URL` | `http://pi-agent:8787` | Pi endpoint used by the voice gateway. |
| `AGENT_FILLER_THRESHOLD_SECONDS` | `0.3` | Delay before optional neutral progress speech. |
| `PI_AGENT_DATA_VOLUME` | `chief-os_pi_agent_data` | Pi OAuth credentials, catalog, and agent runtime state. |
| `PI_AUTH_FILE` | `/root/.pi/agent/auth.json` | Host Pi credential file read only by the setup profile. |
| `PIPELINE_APP_PORT` | `7860` | Browser application host port. |
| `PIPELINE_TLS` | `true` | Enables the built-in self-signed HTTPS certificate. |
| `FASTER_WHISPER_DEVICE` | `cuda` | Faster Whisper inference device. |
| `FASTER_WHISPER_COMPUTE_TYPE` | `float16` | Faster Whisper CTranslate2 precision. |
| `FASTER_WHISPER_NO_SPEECH_PROB` | `0.4` | No-speech filtering threshold. |
| `FASTER_WHISPER_MODEL` | `deepdml/faster-whisper-large-v3-turbo-ct2` | Hugging Face model prefetched by `model-init`. |
| `HF_DOWNLOAD_WORKERS` | `1` | Parallel Hugging Face downloads; one is safest for resumable startup. |
| `HF_HUB_DISABLE_XET` | `true` | Uses standard resumable Hugging Face downloads instead of Xet. |
| `HF_TOKEN` | Empty | Optional Hugging Face token for higher download rate limits. |
| `ONNX_PROVIDER` | `CUDAExecutionProvider` | Kokoro ONNX execution provider. |
| `CHAT_HISTORY_RECENT_TURNS` | `20` | Number of recent messages retained in Talker context. |
| `PIPELINE_IDLE_TIMEOUT_SECS` | `600` | Disconnect timeout; values below `300` are rejected. |
| `AUDIO_OUT_10MS_CHUNKS` | `10` in `.env.example` | Number of 10 ms output-audio chunks buffered by the transport. |
| `ENABLE_ASR_AUDIO_DUMP` | `false` | Writes per-turn microphone WAV files when enabled. |
| `ENABLE_TTS_AUDIO_DUMP` | `false` | Writes per-turn synthesized WAV files when enabled. |
| `ENABLE_TRACING` | `false` | Enables OpenTelemetry tracing. |
| `OTEL_CONSOLE_EXPORT` | `false` | Mirrors enabled traces to the service log. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `localhost:4317` | OTLP collector endpoint used when tracing is enabled. |
| `MODEL_CACHE_VOLUME` | `chief-os_model_cache` | Docker volume for downloaded speech models and package caches. |

Existing deployments may keep the previous named-volume values in `.env`; changing a volume name creates a new empty volume instead of migrating data.

Recreate services after changing `.env`:

```bash
docker compose up -d --force-recreate
```

## Pi Agent Service

Ava is the Chief of Staff. The `pi-agent` service creates one in-memory primary execution `AgentSession` for each voice connection. The primary Pi agent can call `delegate_task` to create a bounded ephemeral worker session. Primary sessions last until the service restarts; long-term personal memory is not implemented yet.

The service mounts only `./workspace` at `/workspace`. The container runs as the non-root `node` user, drops Linux capabilities, uses a read-only root filesystem, and does not receive the Docker socket.

Each request has a correlation ID. `voice-agent` logs Pi request start and completion, while `pi-agent` emits structured `request_received`, `request_completed`, `request_failed`, and `request_aborted` audit events with the same ID. Delegated workers emit corresponding worker events. Audit records include timing and character counts but not user messages, model responses, prompts, or credentials.

The default tools are read-only:

```dotenv
PI_AGENT_TOOLS=read,grep,find,ls
```

To permit file changes and commands inside the workspace, explicitly enable the additional tools:

```dotenv
PI_AGENT_TOOLS=read,grep,find,ls,edit,write,bash
```

The current prototype does not provide a browser approval dialog. Enabling `bash`, `edit`, or `write` grants those tools for every request in that deployment. Keep the service private and never place credentials in `workspace/`. The product policy for future purchase tools requires explicit approval, but no purchase tool is currently exposed.

Compose still accepts the legacy `CHIEF_PI_PROVIDER`, `CHIEF_PI_MODEL`, `CHIEF_PI_THINKING_LEVEL`, `CHIEF_PI_TOOLS`, and `CHIEF_PI_MAX_WORKERS` names as fallback aliases. Prefer the `PI_AGENT_*` names for new configuration.

## Language Models

The roles use separate providers and credentials:

- The Talker uses OpenRouter `google/gemini-3.7-flash`, configured in `src/examples/frontend_backend_agent/services.local.yaml`.
- The primary Pi agent and delegated workers use the built-in `openai-codex/gpt-5.6-sol` catalog entry with a ChatGPT Plus/Pro Codex-plan OAuth credential.

Do not add the OpenRouter `:batch` suffix to the Talker model. The Talker must support OpenAI-compatible `tools` and `tool_choice`.

Authenticate host Pi with `/login` and select **ChatGPT Plus/Pro (Codex)**. Then copy the credential into the private Docker volume:

```bash
docker compose --profile setup run --rm pi-auth-init
docker compose up -d --force-recreate pi-agent voice-agent
```

`pi-auth-init` reads `PI_AUTH_FILE`, copies it with mode `0600` and ownership for the non-root Pi service, and then exits. It does not run during normal startup. Pi automatically refreshes the copied OAuth token in `PI_AGENT_DATA_VOLUME`.

## Prompts and Persona

The only exposed prompt is `chief` in `src/examples/frontend_backend_agent/prompts.yaml`; it controls Ava's Chief-of-Staff behavior.

The primary Pi agent and worker system prompts are in `pi-agent-service/src/server.mjs`.

Restart the affected services after editing prompts:

```bash
docker compose restart voice-agent pi-agent
```

## Speech

The one-shot `model-init` service downloads Faster Whisper and Kokoro before `voice-agent` starts, loads Faster Whisper with the configured CUDA device, and parses Kokoro with `CUDAExecutionProvider`. Artifacts are stored in `MODEL_CACHE_VOLUME`, so image rebuilds and container recreation do not download them again. A missing, partial, or corrupt artifact is downloaded again atomically.

The expected startup order is:

1. `model-init` downloads or verifies both speech models on GPU 0.
2. `model-init` exits with status `0`.
3. Compose starts `voice-agent` after the successful exit.
4. Each browser connection loads the cached models into GPU memory for its session.

To follow first-start progress:

```bash
docker compose logs -f model-init
```

Faster Whisper and Kokoro run in the voice-agent process on GPU 0 after the prefetch completes. Docker exposes the device and provides the CUDA, cuDNN, cuBLAS, cuFFT, and cuRAND library paths. A working session logs `device=cuda` for ASR and `execution_provider=CUDAExecutionProvider` for TTS.

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
