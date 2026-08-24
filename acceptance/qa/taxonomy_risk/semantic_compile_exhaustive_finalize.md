# End-to-end QA: taxonomy semantic compile and exhaustive finalize

Drive only the public `uv run asago-scenario-generator` commands, the
deterministic local OpenAI-compatible fixture, and the documented repository
test/quality commands. Do not import project modules or contact a live model.
Use valid offline taxonomy inputs, a reviewed capability profile, qualification
facts, a reviewed projection context, and a fresh output directory per case.

The fixture must record complete provider request bodies, including each
`response_format.json_schema.schema`, and expose independent response scripts
for actor, narrative, tree, behavior, and candidate-filter requests.

## QA-TSCEF-01: one provider call compiles a valid draft

1. Run `generate` with one qualified projected candidate and one valid draft
   for each of actor, narrative, tree, and behavior.
2. Verify each stage helper emits exactly one provider request per lifecycle
   invocation.
3. Inspect the captured request schema and confirm it accepts only
   request-local handles, not canonical projection IDs.
4. Inspect the published artifact and confirm the compiler attached the
   projection-owned identities, actions, zones, techniques, realizations, or
   postconditions for that stage.
5. Inspect `finalization-inventory.json` and confirm accepted-draft evidence
   retains request digest, response digest, handle map, effective controls,
   and validation result.

**Expected:** The model authors request-local semantics. Deterministic
compilation publishes the canonical artifact. Finalization, not the stage
helper, owns any later retry.

## QA-TSCEF-02: invalid drafts fail closed after one adapter call

1. Script one semantically invalid actor draft, one narrative draft with
   incomplete handle coverage, one narrative draft that groups across
   canonical boundaries, one tree draft with illegal handle coverage, and one
   behavior draft with unknown or duplicate step IDs.
2. For each case, run `generate` against a single target.
3. Verify the targeted stage makes exactly one provider request, publishes no
   compiled artifact, and records a typed retryable failure with the draft
   digest retained.
4. Repeat with a compiler defect after a parseable actor draft.
5. Verify that compiler defect is nonretryable and does not issue a second
   provider request.

**Expected:** Draft validation failures stay on the candidate. Compiler
defects are terminal. No stage helper retries internally.

## QA-TSCEF-03: presentation fallback cannot replace required structure

1. Return a valid narrative draft whose title is missing or empty and whose
   causal grouping is complete.
2. Complete the run and inspect the published narrative plus stage evidence.
3. Verify any replacement title is recorded as a declared presentation
   fallback.
4. Verify step grouping, projected-step coverage, and realizations still
   match the draft and projection context.

**Expected:** Deterministic code may repair presentation text. It must not
invent or drop required semantic structure.

## QA-TSCEF-04: provider schemas omit compiler-owned fields

1. Capture the actor, narrative, tree, and behavior request schemas from a
   successful generate run.
2. Verify the actor schema has no access-provenance or canonical entry-point
   fields.
3. Verify the narrative step schema has no `realizations` property and does
   not ask for projection-owned step IDs.
4. Verify tree and behavior schemas omit canonical realizations, Gherkin
   syntax, and projection-owned postcondition IDs.
5. Recursively audit every generated string and array in those draft schemas
   for finite `maxLength` / `maxItems`.

**Expected:** Compiler-owned data is derived after parsing. Draft schemas stay
bounded.

## QA-TSCEF-05: filter ordinals cannot admit a scenario alone

1. Run generate so the candidate-filter prompt labels candidates with `cN`
   ordinals.
2. Script one exact-set success case and separate cases for an unknown
   ordinal, a missing ordinal, a duplicate ordinal, and a raw canonical
   candidate ID.
3. Verify the success case resolves each ordinal to the matching canonical
   candidate.
4. Verify each defect retains only deterministic-rule-eligible candidates,
   records warning evidence, and does not admit a scenario from the advisory
   filter.

**Expected:** Compact ordinals stay request-local. An irreconcilable advisory
filter is not an admission path.

## QA-TSCEF-06: exhaustive planning creates one target per candidate

1. Prepare five qualified projected candidates across two feasible ingresses.
2. Run generate with `--generation-mode exhaustive` and inspect the coverage
   plan plus finalization inventory.
3. Verify five durable one-choice targets are created and that target IDs are
   distinct from canonical ingress IDs.
4. Repeat with `--generation-mode coverage`.
5. Verify coverage mode creates one bounded fallback queue per feasible
   ingress and stops that target after its first admission.
6. Verify both modes still report coverage by canonical ingress.

**Expected:** Exhaustive mode is the default corpus policy. Coverage mode
remains the bounded smoke-run policy.

## QA-TSCEF-07: one target failure does not skip the remaining corpus

1. In exhaustive mode, script the first target to quarantine or fail
   admission and the remaining targets to succeed.
2. Inspect the run manifest, finalization inventory, and resume keys.
3. Verify the remaining targets still finalize.
4. Verify lifecycle, persistence, and resume records are keyed by the
   distinct finalization target ID.

**Expected:** An admission or quarantine affects only that candidate.

## QA-TSCEF-08: projection-preflight needs no model client

1. Run `asago-scenario-generator projection-preflight` with a reviewed
   profile and fact files that include absent, unknown, stale, and
   contradictory readings.
2. Verify the process constructs no model client and prints a
   machine-readable readiness report.
3. Verify each required fact is classified as absent, unknown, stale, or
   contradictory as scripted.
4. Request a facts template and verify it writes a complete unknown-valued
   template without overwriting an existing file.
5. Verify omitted generation facts record `omitted_compatibility` in manifest
   configuration when generate continues without those facts.

**Expected:** Readiness inspection is offline and does not guess readings.

## QA-TSCEF-09: manifest and report expose four-stage semantic evidence

1. Complete a generate run in which actor, narrative, tree, and behavior all
   accept compiled drafts.
2. Inspect `run-manifest.yaml` `semantic_generation`.
3. Verify it states that all four stages were accepted and retains bounded
   `stage_records`.
4. Inspect the HTML report and verify semantic status is presented separately
   from presentation status.

**Expected:** A manifest can distinguish a fully model-authored scenario from
a failed or cosmetically repaired draft.

## QA-TSCEF-10: authorized length retry stays outside the semantic budget

1. For each of actor, narrative, tree, and behavior, script two consecutive
   `finish_reason: "length"` responses.
2. Run generate against one target.
3. Verify the stage helper makes one provider request per invocation and
   finalization invokes that stage exactly twice.
4. Verify the terminal code is `semantic_draft_length_failed`.
5. Verify the stage semantic owner-retry counter is unchanged.
6. Repeat with one non-length semantic violation followed by a valid draft
   and confirm the existing semantic budget remains the initial attempt plus
   one owner retry.

**Expected:** Length routing cannot consume or expand the semantic retry
budget. A second length failure is terminal for that candidate.
