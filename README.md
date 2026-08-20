# G Force Voice Agent

A standalone flight-booking voice agent built with Pipecat. It supports microphone and typed browser input, speaks responses, and delegates flight searches, bookings, and PNR status checks to a stateful booking service.

This project was extracted from NVIDIA Nemotron Voice Agent and retains the required NVIDIA and third-party notices.

## Runtime Stack

- **Talker and Thinker:** OpenRouter `google/gemini-3.7-flash`
- **Speech recognition:** Faster Whisper Large V3 Turbo on NVIDIA GPU 0
- **Speech synthesis:** Kokoro ONNX with CUDA Execution Provider on NVIDIA GPU 0
- **Browser transport:** WebRTC or WebSocket
- **Backend:** Local G Force Airlines booking API and SQLite database
- **Interface:** Voice input, typed messages, transcripts, service controls, and metrics

The automatic welcome is disabled. The agent waits for the first spoken or typed message.

## Requirements

- Linux x86-64
- NVIDIA GPU with CUDA support; the current deployment targets an RTX 3090 with 24 GB VRAM
- Docker Engine and Docker Compose
- NVIDIA Container Toolkit
- OpenRouter API key

For Docker inside a Proxmox LXC, the NVIDIA runtime can require `no-cgroups = true` in `/etc/nvidia-container-runtime/config.toml`.

## Start

1. Create the environment file:

   ```bash
   cp .env.example .env
   ```

2. Set your key in `.env`:

   ```dotenv
   OPENROUTER_API_KEY=your-key
   ```

3. Build and start both services:

   ```bash
   docker compose up -d --build
   ```

4. Open the browser interface:

   ```text
   https://localhost:7860/
   ```

   Replace `localhost` with the server IP when connecting remotely. Accept the self-signed certificate, connect, and then speak or type a message.

5. Check health and logs:

   ```bash
   docker compose ps
   docker compose logs -f voice-agent booking-server
   ```

6. Stop the deployment without deleting models or bookings:

   ```bash
   docker compose down
   ```

Do not use `docker compose down -v` unless you intend to delete project-owned model and booking volumes.

## Existing Deployment Data

The local, Git-ignored `docker-compose.override.yml` points to the original deployment's model-cache and booking-data volumes. This avoids downloading Faster Whisper and Kokoro again and preserves the current booking database.

Delete that local override to use independent volumes. The standalone Compose defaults are:

```dotenv
MODEL_CACHE_VOLUME=g-force-voice-agent_model_cache
BOOKING_DATA_VOLUME=g-force-voice-agent_booking_data
```

The first independent session downloads the speech models.

## Customize

- Edit the Talker and Thinker prompts in `src/examples/frontend_backend_agent/prompts.yaml`.
- Edit model, voice, and speech settings in `src/examples/frontend_backend_agent/services.local.yaml`.
- Edit the airline tools and workflow in `src/examples/frontend_backend_agent/airline/`.
- Edit the browser interface in `client/src/`.
- Set `welcome_message: true` in `examples_registry.yaml` to restore the automatic greeting.

Refer to [Configuration](docs/CONFIGURATION.md) for the main settings and [Troubleshooting](docs/TROUBLESHOOTING.md) for common failures.

## Development

Install dependencies and run checks from the project root:

```bash
uv sync --dev
uv run pytest tests/ -v
uvx ruff@0.15.6 check .
uvx ruff@0.15.6 format --check .
npm --prefix client ci
npm --prefix client run lint
npm --prefix client run build
```

Run the server without Docker only after starting the booking server and exporting `PLATFORM=consumergpu`. Docker is recommended because it provides the verified CUDA library paths.

## Project Layout

```text
client/                              Browser interface
src/server.py                        FastAPI and Pipecat transport server
src/examples/shared/                 Shared pipeline runtime helpers
src/examples/frontend_backend_agent/ Talker, Thinker, prompts, and airline workflow
docker/Dockerfile                    GPU-capable application image
docker-compose.yml                   Voice agent and booking server deployment
examples_registry.yaml               Single exposed agent and UI defaults
pyproject.toml / uv.lock              Python dependencies
```

## Security

- `.env` is ignored by Git. Never commit API keys.
- Use a trusted TLS certificate for production.
- Restrict ports `7860` and `8001` with your firewall.
- Replace or protect the demonstration booking database before handling real customer data.

## License

The project retains the upstream BSD-2-Clause [`LICENSE`](LICENSE), source copyright headers, and [`third_party_oss_license.txt`](third_party_oss_license.txt). Review dependency licenses before redistribution.
