"""Tier 1 deterministic evaluation framework for asago-scenario-generator.

Provides no-model-call metrics for assessing generated scenario quality:
- Cross-layer consistency
- Gherkin well-formedness
- Taxonomy grounding
- Batch diversity
"""

from asago_scenario_generator.eval.consistency import score_consistency
from asago_scenario_generator.eval.diversity import score_diversity
from asago_scenario_generator.eval.gherkin import score_gherkin
from asago_scenario_generator.eval.grounding import score_grounding
from asago_scenario_generator.eval.plausibility import score_plausibility
from asago_scenario_generator.eval.runner import run_evaluation

__all__ = [
    "score_consistency",
    "score_diversity",
    "score_gherkin",
    "score_grounding",
    "score_plausibility",
    "run_evaluation",
]
