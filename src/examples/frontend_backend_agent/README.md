# G Force Frontend/Backend Agent

This package contains the standalone agent pipeline:

- `pipeline.py` builds the Faster Whisper, Gemini Talker, Thinker, and Kokoro pipeline.
- `prompts.yaml` defines the user-facing and planning prompts.
- `services.local.yaml` configures OpenRouter and GPU speech services.
- `airline/` implements flight search, booking, and PNR status workflows.
- `src/` implements planning, protocol, tool handlers, and TTS filtering.

Run and configure the complete project through the [project README](../../../README.md).
