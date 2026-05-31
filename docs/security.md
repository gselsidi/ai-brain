# Security Notes

The framework is local and product-agnostic, but the SDLC team should still
review:

- unsafe file handling
- dependency vulnerabilities
- unsafe automation permissions
- secret leakage in memory, logs, or reports
- prompt injection in docs or external content
- overbroad agent tool access
- missing adoption-boundary warnings

Blocking data safety or automation safety issues fail the release gate.
