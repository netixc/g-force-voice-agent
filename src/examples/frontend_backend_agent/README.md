# Ava Frontend/Backend Agent

This package contains the standalone voice pipeline:

- `pipeline.py` builds the Faster Whisper, Gemini Talker, Pi backend client, and Kokoro pipeline.
- `prompts.yaml` defines Ava's Chief-of-Staff behavior.
- `services.local.yaml` configures OpenRouter, the Pi endpoint, and GPU speech services.
- `src/pi_backend.py` adapts one remote Pi session to the Pipecat tool boundary.
- The repository-level `src/prefetch_models.py` downloads and validates cached Whisper and Kokoro artifacts before startup.

The Node-based Pi SDK service lives in the repository-level `pi-agent-service/` directory. Ava is the Chief of Staff and routes substantive requests to a persistent primary Pi execution session, which can delegate bounded tasks to ephemeral workers. Run and configure the complete project through the [project README](../../../README.md).
