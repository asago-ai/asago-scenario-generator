Feature: Taxonomy semantic compile and exhaustive finalize
  Taxonomy generation authors actor intent, narrative causality, attack-tree
  topology, and behavior interactions as request-local drafts. Pure compilers
  resolve those handles to projection-owned identities after the draft passes.
  Finalization owns retries. The default generation policy creates one durable
  target per qualified candidate.

  # Taxonomy semantic compile and exhaustive finalize 01 compiles one valid draft per stage
  Scenario Outline: Taxonomy semantic compile and exhaustive finalize 01 compiles one valid draft per stage
    Given a qualified projected candidate with request-local handles for "<stage>"
    And the fixture returns one valid "<stage>" semantic draft
    When the "<stage>" stage runs one lifecycle invocation
    Then the stage adapter makes exactly 1 provider request
    And the provider schema accepts only request-local handles
    And the compiler attaches the canonical projection-owned identities
    And accepted-draft evidence retains the request digest, response digest, handle map, and validation result

    Examples:
      | stage     |
      | actor     |
      | narrative |
      | tree      |
      | behavior  |

  # Taxonomy semantic compile and exhaustive finalize 02 fails closed for invalid drafts
  Scenario Outline: Taxonomy semantic compile and exhaustive finalize 02 fails closed for invalid drafts
    Given a qualified projected candidate with request-local handles for "<stage>"
    And the fixture returns a "<stage>" draft with defect "<defect>"
    When the "<stage>" stage runs one lifecycle invocation
    Then the stage adapter makes exactly 1 provider request
    And the outcome is a typed "<retryability>" failure
    And no compiled "<stage>" artifact is published
    And failed-draft evidence retains the draft digest and retryability

    Examples:
      | stage     | defect                         | retryability  |
      | actor     | semantically invalid fields    | retryable     |
      | narrative | incomplete handle coverage     | retryable     |
      | narrative | grouping across boundaries     | retryable     |
      | tree      | illegal handle coverage        | retryable     |
      | behavior  | unknown or duplicate step IDs  | retryable     |
      | actor     | compiler defect after parse    | nonretryable  |

  # Taxonomy semantic compile and exhaustive finalize 03 keeps presentation fallback explicit
  Scenario: Taxonomy semantic compile and exhaustive finalize 03 keeps presentation fallback explicit
    Given a valid narrative draft whose title is missing or empty
    When the narrative compiler finalizes that draft
    Then deterministic code may replace only presentation text
    And the required semantic structure is unchanged
    And accepted-draft evidence records the declared presentation fallback

  # Taxonomy semantic compile and exhaustive finalize 04 excludes compiler-owned fields from drafts
  Scenario Outline: Taxonomy semantic compile and exhaustive finalize 04 excludes compiler-owned fields from drafts
    Given the "<stage>" provider response schema is captured
    When the schema is inspected
    Then it does not ask the provider for "<excluded_fields>"
    And every generated string and array in the draft schema remains finitely bounded

    Examples:
      | stage     | excluded_fields                                      |
      | actor     | access provenance and canonical entry-point IDs      |
      | narrative | canonical realizations and projection-owned step IDs |
      | tree      | canonical leaf realizations                          |
      | behavior  | Gherkin syntax and projection-owned postcondition IDs |

  # Taxonomy semantic compile and exhaustive finalize 05 uses compact filter ordinals
  Scenario Outline: Taxonomy semantic compile and exhaustive finalize 05 uses compact filter ordinals
    Given the candidate filter prompt labels candidates with request-local ordinals
    And the fixture returns filter decisions "<decisions>"
    When the filter response is reconciled
    Then reconciliation "<outcome>"
    And an irreconcilable advisory filter cannot admit a scenario by itself

    Examples:
      | decisions                         | outcome                                      |
      | one decision per expected ordinal | resolves each ordinal to a canonical ID      |
      | an unknown ordinal                | retains deterministic-rule-eligible candidates with warning evidence |
      | a missing ordinal                 | retains deterministic-rule-eligible candidates with warning evidence |
      | a duplicate ordinal               | retains deterministic-rule-eligible candidates with warning evidence |
      | a canonical candidate ID          | retains deterministic-rule-eligible candidates with warning evidence |

  # Taxonomy semantic compile and exhaustive finalize 06 plans exhaustive one-choice targets
  Scenario Outline: Taxonomy semantic compile and exhaustive finalize 06 plans exhaustive one-choice targets
    Given <qualified_count> qualified projected candidates across <ingress_count> feasible ingresses
    And generation mode is "<mode>"
    When generation planning builds finalization targets
    Then the plan contains <target_count> durable targets
    And each target identity is distinct from canonical ingress identity
    And coverage is still reported by canonical ingress

    Examples:
      | qualified_count | ingress_count | mode       | target_count |
      | 5               | 2             | exhaustive | 5            |
      | 5               | 2             | coverage   | 2            |

  # Taxonomy semantic compile and exhaustive finalize 07 isolates admission to one target
  Scenario: Taxonomy semantic compile and exhaustive finalize 07 isolates admission to one target
    Given exhaustive mode created one target per qualified candidate
    And the first target is quarantined or fails admission
    When the remaining targets finalize
    Then no other target is skipped because of that failure
    And lifecycle, persistence, and resume keys use the failed target ID

  # Taxonomy semantic compile and exhaustive finalize 08 reports projection readiness without a model
  Scenario Outline: Taxonomy semantic compile and exhaustive finalize 08 reports projection readiness without a model
    Given a reviewed capability profile and qualification facts with status "<fact_status>"
    When the public projection-preflight command runs
    Then no model client is constructed
    And the report classifies that fact as "<fact_status>"
    And a complete unknown-valued facts template can be written without overwriting

    Examples:
      | fact_status    |
      | absent         |
      | unknown        |
      | stale          |
      | contradictory  |

  # Taxonomy semantic compile and exhaustive finalize 09 persists four-stage semantic evidence
  Scenario: Taxonomy semantic compile and exhaustive finalize 09 persists four-stage semantic evidence
    Given all four semantic stages accept a compiled draft
    When the run manifest and HTML report are written
    Then semantic_generation states that all four stages were accepted
    And bounded stage_records retain digest, handle-map, control, and fallback evidence
    And the HTML report presents semantic status separately from presentation status

  # Taxonomy semantic compile and exhaustive finalize 10 keeps length retries out of semantic budget
  Scenario Outline: Taxonomy semantic compile and exhaustive finalize 10 keeps length retries out of semantic budget
    Given the first "<stage>" provider response ends with finish reason "length"
    And the authorized length retry also ends with finish reason "length"
    When finalization runs the candidate lifecycle
    Then the stage helper makes exactly 1 provider request per invocation
    And finalization invokes the stage exactly 2 times
    And the terminal code is "semantic_draft_length_failed"
    And the semantic owner-retry counter is unchanged

    Examples:
      | stage     |
      | actor     |
      | narrative |
      | tree      |
      | behavior  |
