# Ava Frontend/Backend Agent

This package contains the standalone voice pipeline:

- `pipeline.py` builds the Faster Whisper, Gemini Talker, Pi backend client, and Kokoro pipeline.
- `prompts.yaml` defines the default chief-of-staff voice facade and preserved airline prompts.
- `services.local.yaml` configures OpenRouter, the Pi endpoint, and GPU speech services.
- `src/pi_backend.py` adapts one remote Pi session to the Pipecat tool boundary.
- `airline/` preserves the demonstration flight search, booking, and PNR workflow.

The Node-based Pi SDK service lives in `pi-agent-service/`. Run and configure the complete project through the [project README](../../../README.md).
