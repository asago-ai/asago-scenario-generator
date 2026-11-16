# Asago Scenario Generator

Pre-alpha adversarial-scenario generation for AI systems, with taxonomy/risk
and STPA workflows maintained as peer product surfaces.

## Commands

```bash
uv sync --locked
./scripts/quality.sh
uv run pytest tests/ -q
```

Deterministic tests must not contact an LLM endpoint.

## Architecture

- `src/asago_scenario_generator/` contains shared domain models, the
  taxonomy/risk pipeline, the STPA pipeline, CLI, evaluation, and reporting.
- `data/` contains committed schemas, taxonomies, mappings, and qualification
  inputs.
- `config/` contains sanitized examples and portable project configuration.

Read `docs/architecture/overview.md` before changing cross-pipeline contracts.

## Development

- Track durable work and specification approval in GitHub Issues and PRs.
- Preserve both generation approaches unless the issue explicitly changes
  their shared contract.
- Keep harness installations and runtime state local; the repository owns only
  portable methodology, configuration, and scripts.
- Update `README.md`, this file, and linked documentation when an interface or
  workflow changes.
- `AGENTS.md` is a symlink to this file.
