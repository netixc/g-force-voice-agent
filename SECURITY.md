# Security

Do not open a public issue containing API keys, customer information, booking data, private URLs, or infrastructure details.

This repository is a prototype and has not been hardened for production. Before production use, add authentication, authorization, trusted TLS, secret management, rate limiting, audit logging, data-retention controls, and a secured booking integration.

If a credential is committed, revoke it immediately, remove it from Git history, and rotate any related secrets before pushing again.
