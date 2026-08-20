# Documentation Guidance

## Scope

Keep documentation accurate for developers who configure, deploy, and extend this prototype. Verify claims against `docker-compose.yml`, `.env.example`, `examples_registry.yaml`, the service catalog, and pipeline code.

## Style

- Use concise, direct instructions and active voice.
- Keep `README.md` focused on purpose, quick start, customization, and project status.
- Put detailed settings in `docs/CONFIGURATION.md`.
- Put symptoms and fixes in `docs/TROUBLESHOOTING.md`.
- Format commands, paths, settings, and model IDs as code.
- Never include credentials, private URLs, customer data, or unsupported performance claims.
- Preserve NVIDIA attribution, source headers, and license references.

## Required Updates

Update documentation when a change affects:

- Environment variables or defaults
- Compose services, ports, volumes, or GPU behavior
- Models, prompts, voices, transports, or browser controls
- Booking capabilities or user-visible errors
- Setup, validation, or deployment commands

## Validation

Run pre-commit on changed documentation and inspect links manually:

```bash
uv run pre-commit run --files README.md docs/CONFIGURATION.md docs/TROUBLESHOOTING.md
git diff --check
```
