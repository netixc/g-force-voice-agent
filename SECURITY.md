# Security

Do not open a public issue containing API keys, OAuth credentials, customer information, workspace data, private URLs, or infrastructure details.

This repository is a prototype and has not been hardened for production. Before production use, add authentication, authorization, trusted TLS, managed secrets, rate limiting, approval controls, per-user workspace isolation, and explicit data-retention policies.

The Talker uses an OpenRouter API key from private `.env`. Pi uses a ChatGPT Codex OAuth credential stored in the private `PI_AGENT_DATA_VOLUME`; `pi-auth-init` copies only the `openai-codex` entry and never places it in the application image or workspace. Pi resource discovery is disabled, and enabled filesystem tools enforce the canonical `/workspace` boundary. The `bash` tool remains disabled until it can run in a separate sandbox without access to Pi credentials.

If a credential is committed or exposed, revoke it immediately, remove it from Git history, and rotate any related secrets before pushing again.
