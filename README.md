# G Force Voice Agent

A working prototype for a GPU-accelerated airline voice agent. Users can speak or type in the browser, while a fast Talker delegates flight searches, bookings, and PNR checks to a stateful backend agent.

Based on NVIDIA's open source [Nemotron Voice Agent](https://github.com/NVIDIA-AI-Blueprints/nemotron-voice-agent) blueprint and Pipecat. This standalone version keeps only the Frontend/Backend Agent workflow needed for continued customization.

## Stack

- OpenRouter `google/gemini-3.7-flash` for the Talker and Thinker
- Faster Whisper Large V3 Turbo on an NVIDIA GPU
- Kokoro ONNX TTS with CUDA Execution Provider
- Pipecat with WebRTC and WebSocket transports
- React browser UI with voice and typed input
- Local FastAPI booking service and SQLite database

## Requirements

- Linux x86-64 with an NVIDIA CUDA GPU
- Docker Engine, Docker Compose, and NVIDIA Container Toolkit
- OpenRouter API key

The current configuration is verified on an RTX 3090 with 24 GB VRAM.

## Quick Start

```bash
cp .env.example .env
```

Add your key to `.env`:

```dotenv
OPENROUTER_API_KEY=your-key
```

Build and run:

```bash
docker compose up -d --build
docker compose ps
```

Open `https://localhost:7860/`, accept the development certificate, and connect. Replace `localhost` with the server IP for remote access.

```bash
# Follow logs
docker compose logs -f voice-agent booking-server

# Stop without deleting models or bookings
docker compose down
```

## Customize

| Area | Path |
| --- | --- |
| Talker and Thinker prompts | `src/examples/frontend_backend_agent/prompts.yaml` |
| Models, voices, and speech settings | `src/examples/frontend_backend_agent/services.local.yaml` |
| Airline tools and booking flow | `src/examples/frontend_backend_agent/airline/` |
| Browser interface | `client/src/` |
| Deployment and GPU settings | `docker-compose.yml` and `.env` |
| AI coding-agent guidance | `AGENTS.md` and `skills/` |

Refer to [Configuration](docs/CONFIGURATION.md), [Troubleshooting](docs/TROUBLESHOOTING.md), and [Contributing](CONTRIBUTING.md).

## Prototype Status

This is a working prototype intended for further development. The included airline database contains demonstration data. Before production use, add authentication, trusted TLS, persistent production services, access controls, monitoring, and a real booking integration.

## Development

```bash
uv sync --dev
uv run pytest tests/ -v
uv run ruff check .
npm --prefix client ci
npm --prefix client run lint
npm --prefix client run build
```

## Security and License

`.env`, local Compose overrides, model files, and databases are ignored by Git. Never commit credentials or customer data.

The project retains the upstream BSD-2-Clause [`LICENSE`](LICENSE), NVIDIA copyright headers, and [`third_party_oss_license.txt`](third_party_oss_license.txt).
