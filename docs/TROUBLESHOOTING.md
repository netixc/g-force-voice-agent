# Troubleshooting

## No Reply After Sending a Message

Check the voice gateway and Pi service logs:

```bash
docker compose logs --tail 200 voice-agent pi-agent
```

Confirm the Pi service is healthy:

```bash
docker compose ps pi-agent
```

If OpenRouter reports that the model is only available through the Batch API, remove `:batch` from the model ID in `services.local.yaml`.

Confirm `OPENROUTER_API_KEY` is set in `.env`, then recreate the service:

```bash
docker compose up -d --force-recreate voice-agent pi-agent
```

## Pi Cannot Read or Modify Workspace Files

Place only the files the assistant needs under `./workspace`. The default `CHIEF_PI_TOOLS` setting is read-only. Add `edit`, `write`, or `bash` only when you intentionally grant those capabilities.

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

## First Session Is Slow

The first independent session downloads Faster Whisper and Kokoro. Later sessions reuse `MODEL_CACHE_VOLUME`.

Check the cache:

```bash
docker volume inspect "$(grep '^MODEL_CACHE_VOLUME=' .env | cut -d= -f2-)"
```

## Browser Cannot Use the Microphone

Use HTTPS. Browser microphone and WebRTC APIs generally require a secure context. Accept the self-signed certificate at `https://<server-ip>:7860/`, or install a trusted production certificate.

## Duplicate Greeting

The project disables the automatic welcome. If you enabled it and then type `hello` while it is speaking, the model can generate 2 similar greetings. Set `welcome_message: false` in `examples_registry.yaml` to wait for the first user message.

## Ports Are Already Allocated

Either stop the other deployment or change these `.env` values:

```dotenv
PIPELINE_APP_PORT=7861
BOOKING_SERVER_PORT=8002
```

Then run `docker compose up -d` again.

## ONNX Thread-Affinity Warnings

ONNX Runtime can print `pthread_setaffinity_np failed` inside a Proxmox LXC. The warning is nonfatal when synthesis succeeds and `CUDAExecutionProvider` remains active.
