---
name: configure-agent
description: Configure Ava prompts, Talker and Pi models, local speech services, UI defaults, and environment settings.
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
2. Preserve `OPENROUTER_API_KEY` in private `.env` and Codex OAuth in `PI_AGENT_DATA_VOLUME`; never print or commit either credential.
3. Keep the Talker on an interactive, tool-capable OpenRouter model without the `:batch` suffix.
4. Keep the primary Pi agent and workers on the configured built-in `openai-codex/gpt-5.6-sol` model unless the request explicitly changes it.
5. Keep Faster Whisper and Kokoro on GPU 0 unless the request explicitly changes hardware placement.
6. Restart `voice-agent` after YAML or prompt changes:

   ```bash
   docker compose restart voice-agent
   ```

7. Recreate services after `.env` changes:

   ```bash
   docker compose up -d --force-recreate
   ```

8. Update `README.md` or `docs/CONFIGURATION.md` for user-visible defaults.

## Validation

```bash
uv run pytest tests/ -v
uv run ruff check .
docker compose config
docker compose logs --tail 200 voice-agent
```
