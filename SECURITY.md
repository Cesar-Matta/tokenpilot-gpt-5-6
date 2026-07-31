# Security policy

Do not open a public issue for a suspected vulnerability. Report it privately to the repository maintainers with a minimal reproduction, affected version, impact, and suggested mitigation when possible.

Security-sensitive deployment defaults:

- Enable `REQUIRE_API_KEY` in production.
- Store `OPENAI_API_KEY` and router keys in a secret manager.
- Put the service behind TLS and an API gateway or identity layer.
- Keep prompts and responses out of logs unless an explicit privacy review authorizes it.
- Use a shared rate limiter before deploying multiple replicas.
