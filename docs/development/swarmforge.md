# SwarmForge development methodology

This repository uses the harness-independent SwarmForge methodology. The
method is normative; any particular agent harness, role installation, or
handoff runtime is replaceable and remains untracked.

## Work contract

GitHub Issues are the durable source of work and decisions. An approved issue
is the approved specification unless an implementation-relevant ambiguity is
discovered. Branches and pull requests carry the implementation, evidence, and
review discussion.

A work item is ready when its behavior, constraints, exclusions, and observable
acceptance criteria are clear. If they are not clear, resolve them in the issue
before implementation.

## The six-pack

The six roles are a sequence of responsibilities, not a requirement for six
processes or a specific harness:

1. **Specifier** — sharpen the issue into observable behavior and acceptance
   examples; identify ambiguity rather than inventing product decisions.
2. **Coder** — work test-first in vertical slices and implement the smallest
   behavior that satisfies each accepted example.
3. **Cleaner** — simplify names, boundaries, duplication, and coupling without
   changing accepted behavior.
4. **Hardener** — exercise error paths, properties, mutation resistance, and
   adversarial inputs; make failures explicit and diagnosable.
5. **QA** — run independent deterministic and acceptance gates, verify the
   issue contract, and report reproducible evidence.
6. **Architect** — review the completed slice for contract coherence, module
   boundaries, and durable documentation before merge.

Scaffolding a new language or acceptance runtime is bootstrap work outside the
six-pack. Once the project commands exist, every feature follows the six
responsibilities even when one contributor performs several roles.

## Acceptance pipeline

Gherkin in `features/` is committed source. The normal pipeline is:

```text
feature -> APS JSON IR -> IR DRY report -> generated pytest entrypoint
        -> committed acceptance runtime/handler -> project behavior
```

Run generation and generated tests sequentially with
`./scripts/acceptance.sh`. Generated artifacts under `build/acceptance/` and
mutation workspaces are disposable. Step handlers should use regular-expression
captures for repeated shapes and separate literal handlers only for genuinely
different behavior.

Live-model scenarios require `ASAGO_SCENARIO_GENERATOR_QA_PIPELINE=1`.
Everything else must run without a reachable LLM endpoint.

## Quality sequence

The normal merge evidence is:

```bash
./scripts/quality.sh
uv run pytest tests/ -q
./scripts/acceptance.sh
```

Changed production code should also be evaluated with the configured coverage,
CRAP, DRY, source mutation, and Gherkin mutation commands where relevant. The
project target is CRAP at or below 6 and mutation score at or above 80. Tool
scope remains `src/`; Ruff also checks `acceptance/`.

## External tools and pins

`config/swarmforge.env` records repository URLs, exact revisions, commands, and
paths. It does not install anything. A developer or CI job explicitly checks
out or installs those revisions after granting the required network and
installation permissions.

The APS checkout is discovered through
`ASAGO_SCENARIO_GENERATOR_APS_ROOT`, then through the ignored local paths
`.cache/acceptance-pipeline-specification/` and
`tmp/Acceptance-Pipeline-Specification/`. Invalid explicit configuration fails
immediately; the project never silently downloads a replacement.

Update a pin in a dedicated pull request that records upstream changes and runs
the affected quality gate. Harness-specific role prompts, handoff files,
dashboards, Beads state, and local tool clones are not repository content.

## Completion

A pull request is complete when the issue contract is satisfied, deterministic
gates pass without an endpoint, opt-in behavior is clearly separated, generated
or harness state is absent from the diff, and documentation reflects changed
interfaces. Organization administrators own branch-protection configuration.
