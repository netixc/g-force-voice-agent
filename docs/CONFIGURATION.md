# Configuration

## Environment

The deployment reads `.env` through Docker Compose.

| Setting | Default | Purpose |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | Required | Authenticates both Gemini language model roles. |
| `OPENROUTER_APP_NAME` | `G Force Voice Agent` | OpenRouter attribution title. |
| `PIPELINE_APP_PORT` | `7860` | Browser application host port. |
| `BOOKING_SERVER_PORT` | `8001` | Booking API host port. |
| `PIPELINE_TLS` | `true` | Enables the built-in self-signed HTTPS certificate. |
| `FASTER_WHISPER_DEVICE` | `cuda` | Faster Whisper inference device. |
| `FASTER_WHISPER_COMPUTE_TYPE` | `float16` | Faster Whisper CTranslate2 precision. |
| `FASTER_WHISPER_NO_SPEECH_PROB` | `0.4` | No-speech filtering threshold. |
| `ONNX_PROVIDER` | `CUDAExecutionProvider` | Kokoro ONNX execution provider. |
| `CHAT_HISTORY_RECENT_TURNS` | `20` | Number of recent messages retained in Talker context. |
| `MODEL_CACHE_VOLUME` | `g-force-voice-agent_model_cache` | Docker volume for downloaded speech models and package caches. |
| `BOOKING_DATA_VOLUME` | `g-force-voice-agent_booking_data` | Docker volume for SQLite booking state. |

Restart after changing `.env`:

```bash
docker compose up -d
```

## Language Models

Edit `src/examples/frontend_backend_agent/services.local.yaml` to change the Talker and Thinker models. Both roles currently use:

```yaml
model_id: "google/gemini-3.7-flash"
base_url: "https://openrouter.ai/api/v1"
extra_params: '{"extra_body":{"reasoning":{"effort":"low"}}}'
```

Do not add the `:batch` suffix. OpenRouter accepts that variant through its asynchronous Batch API, while Pipecat requires interactive chat completions.

A replacement model must support OpenAI-compatible `tools` and `tool_choice` for the airline workflow.

## Prompts and Persona

Edit `src/examples/frontend_backend_agent/prompts.yaml`:

- `talker` controls the user-facing Ava persona and tool delegation.
- `thinker` controls structured planning for flight tools.

Restart the voice-agent service after editing a prompt:

```bash
docker compose restart voice-agent
```

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

Change the host-side ports when another deployment already uses `7860` or `8001`:

```dotenv
PIPELINE_APP_PORT=7861
BOOKING_SERVER_PORT=8002
```

The containers continue to use ports `7860` and `8001` internally.
