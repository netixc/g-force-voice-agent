---
name: configure-agent
description: Configure the G Force Voice Agent prompts, OpenRouter models, local speech services, UI defaults, and environment settings.
version: "1.0.0"
---

# Configure Agent

## Scope

Use this workflow for changes to:

- `.env.example`
- `examples_registry.yaml`
- `src/examples/frontend_backend_agent/prompts.yaml`
- `src/examples/frontend_backend_agent/services.local.yaml`
- Talker, Pi agent, ASR, TTS, and welcome-message defaults

## Procedure

1. Identify the smallest configuration surface that satisfies the request.
2. Preserve `OPENROUTER_API_KEY` in the private `.env`; never print or commit it.
3. Keep the OpenRouter model compatible with interactive chat completions and tool calls. Do not use the `:batch` suffix.
4. Keep Faster Whisper and Kokoro on GPU 0 unless the request explicitly changes hardware placement.
5. Restart `voice-agent` after YAML or prompt changes:

   ```bash
   docker compose restart voice-agent
   ```

6. Recreate services after `.env` changes:

   ```bash
   docker compose up -d --force-recreate
   ```

7. Update `README.md` or `docs/CONFIGURATION.md` for user-visible defaults.

## Validation

```bash
uv run pytest tests/ -v
uv run ruff check .
docker compose config
docker compose logs --tail 200 voice-agent
```
