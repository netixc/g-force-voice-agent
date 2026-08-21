# Ava Frontend/Backend Agent

This package contains the standalone voice pipeline:

- `pipeline.py` builds the Faster Whisper, Gemini Talker, Pi backend client, and Kokoro pipeline.
- `prompts.yaml` defines the chief-of-staff voice facade.
- `services.local.yaml` configures OpenRouter, the Pi endpoint, and GPU speech services.
- `src/pi_backend.py` adapts one remote Pi session to the Pipecat tool boundary.
- `src/prefetch_models.py` downloads and validates cached Whisper and Kokoro artifacts before startup.

The Node-based Pi SDK service lives in `pi-agent-service/`. Ava routes substantive requests to a persistent chief Pi session, which can delegate bounded tasks to ephemeral workers. Run and configure the complete project through the [project README](../../../README.md).
