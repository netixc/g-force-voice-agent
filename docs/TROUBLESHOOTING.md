# Troubleshooting

## No Reply After Sending a Message

Check the voice gateway and Pi service logs:

```bash
docker compose logs --tail 200 voice-agent pi-agent
```

Confirm the Pi service is healthy and correlate requests across both services:

```bash
docker compose ps pi-agent
docker compose logs --tail 200 voice-agent pi-agent | grep -E \
  'Pi request (started|completed)|"event":"request_(received|completed|failed|aborted)"'
```

A successful request has the same `request_id` in the voice gateway's start/completion lines and Pi's structured received/completed events. Audit events intentionally omit request and response content.

If OpenRouter reports that the Talker model is only available through the Batch API, remove `:batch` from the model ID in `services.local.yaml`.

Confirm `OPENROUTER_API_KEY` is set in `.env`, then recreate `voice-agent`:

```bash
docker compose up -d --force-recreate voice-agent
```

If Pi reports missing or expired OpenAI Codex credentials, run `/login` in host Pi and select **ChatGPT Plus/Pro (Codex)**, then resync and restart Pi:

```bash
docker compose --profile setup run --rm pi-auth-init
docker compose up -d --force-recreate pi-agent voice-agent
```

## Pi Cannot Read or Modify Workspace Files

Place only the files the assistant needs under `./workspace`. The default `PI_AGENT_TOOLS` setting is read-only. Add `edit`, `write`, or `bash` only when you intentionally grant those capabilities.

The container runs as a non-root user. If host-created workspace files deny access, update their ownership or permissions without making credentials or unrelated host files accessible.

## CUDA Execution Provider Is Unavailable

Confirm GPU access and ONNX providers:

```bash
docker compose exec voice-agent nvidia-smi
docker compose exec voice-agent uv run python -c \
  'import onnxruntime as o; print(o.get_available_providers())'
```

The provider list must include `CUDAExecutionProvider`. Rebuild the image if it does not:

```bash
docker compose build --no-cache voice-agent
docker compose up -d
```

## Faster Whisper Does Not Use CUDA

Confirm the NVIDIA Container Toolkit exposes GPU 0:

```bash
docker compose exec voice-agent nvidia-smi
```

For Docker inside a Proxmox LXC, NVIDIA cgroup management can fail. Set `no-cgroups = true` in `/etc/nvidia-container-runtime/config.toml` when the LXC host already controls device access.

## Model Download Does Not Finish

The one-shot `model-init` service must finish before `voice-agent` starts. Follow its progress:

```bash
docker compose logs -f model-init
```

Downloads resume in `MODEL_CACHE_VOLUME` after a restart. Set `HF_TOKEN` in `.env` if unauthenticated Hugging Face rate limits prevent completion. Keep `HF_DOWNLOAD_WORKERS=1` and `HF_HUB_DISABLE_XET=true` for reliable resumable downloads.

Check the cache and rerun initialization:

```bash
docker volume inspect "$(grep '^MODEL_CACHE_VOLUME=' .env | cut -d= -f2-)"
docker compose run --rm model-init
```

Do not repeatedly restart `voice-agent` while a model is downloading. `model-init` showing `Exited (0)` is success, not a crashed service.

## First Connection Pauses for a Few Seconds

Model files are downloaded once, but Faster Whisper and Kokoro are instantiated for each browser session. A short first-connection pause while the cached models enter GPU memory is expected. Confirm completion with:

```bash
docker compose logs --tail 200 voice-agent | grep -E \
  'Loaded Whisper model|device=cuda|execution_provider=CUDAExecutionProvider|pipeline is now ready'
```

If the log contains `INVALID_PROTOBUF`, rerun `docker compose run --rm model-init`. The initializer removes partial Kokoro artifacts, downloads them atomically, and validates them before allowing normal startup.

## Browser Cannot Use the Microphone

Use HTTPS. Browser microphone and WebRTC APIs generally require a secure context. Accept the self-signed certificate at `https://<server-ip>:7860/`, or install a trusted production certificate.

## Duplicate Greeting

The project disables the automatic welcome. If you enabled it and then type `hello` while it is speaking, the model can generate 2 similar greetings. Set `welcome_message: false` in `examples_registry.yaml` to wait for the first user message.

## Port Is Already Allocated

Either stop the other deployment or change the browser port in `.env`:

```dotenv
PIPELINE_APP_PORT=7861
```

Then run `docker compose up -d` again.

## ONNX Thread-Affinity Warnings

ONNX Runtime can print `pthread_setaffinity_np failed` inside a Proxmox LXC. It can also report that shape-related nodes were assigned to the CPU. These warnings are nonfatal when the log confirms `execution_provider=CUDAExecutionProvider` and Kokoro produces audio.
