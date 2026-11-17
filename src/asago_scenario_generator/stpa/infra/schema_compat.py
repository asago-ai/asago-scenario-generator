"""Wire-schema compatibility for OpenAI-strict structured outputs (STPA copy).

This module is a clean-copy local implementation: the STPA infra layer may
not import the taxonomy pipeline package (enforced by
``tests/stpa/test_architecture.py``). Keep it in sync with
``asago_scenario_generator.llm.schema_compat``; the parity test asserts the
two produce identical projections.

The OpenAI SDK's ``beta.chat.completions.parse`` requests ``strict: true``
and passes Pydantic's JSON Schema through ``to_strict_json_schema``. Some
supported JSON Schema keywords that Pydantic emits for local validation
(``maxProperties``, ``minLength``, ``maxItems`` …) are not permitted by
strict validators, so a gateway rejects the whole request with a 400 before
the model sees it.

This module projects a response model's schema onto the strict wire
contract without changing the model or its local validation: bounds are
still enforced by Pydantic after parsing, but only supported keywords are
sent to the provider.

Compatibility is opt-in. ``native`` (the default) leaves the request
unchanged; ``strict`` applies the projection.
"""

from __future__ import annotations

import copy
import os
from typing import Any

from pydantic import BaseModel

SCHEMA_COMPAT_ENV = "ASAGO_SCENARIO_GENERATOR_JSON_SCHEMA_COMPAT"
SCHEMA_COMPAT_NATIVE = "native"
SCHEMA_COMPAT_STRICT = "strict"
SCHEMA_COMPAT_MODES = (SCHEMA_COMPAT_NATIVE, SCHEMA_COMPAT_STRICT)

# Keywords emitted by Pydantic for local validation that OpenAI-strict
# validators reject. ``const`` is converted to a one-value ``enum`` rather
# than dropped.
_STRICT_UNSUPPORTED_KEYWORDS = frozenset(
    {
        "maxProperties",
        "minProperties",
        "maxLength",
        "minLength",
        "maxItems",
        "minItems",
        "uniqueItems",
        "pattern",
        "format",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "multipleOf",
        "default",
        "examples",
        "deprecated",
        "readOnly",
        "writeOnly",
        "$comment",
        "propertyNames",
        "patternProperties",
    }
)

_SUBSCHEMA_MAP_KEYS = ("properties", "$defs", "definitions", "dependentSchemas")
_SUBSCHEMA_VALUE_KEYS = ("items", "additionalProperties", "not", "contains")
_SUBSCHEMA_LIST_KEYS = ("anyOf", "allOf", "oneOf", "prefixItems")


def resolve_schema_compat(value: str | None = None) -> str:
    """Resolve the mode from an explicit value or the environment."""
    mode = value if value is not None else os.environ.get(SCHEMA_COMPAT_ENV)
    if not mode:
        return SCHEMA_COMPAT_NATIVE
    normalized = mode.strip().lower()
    if normalized not in SCHEMA_COMPAT_MODES:
        allowed = ", ".join(SCHEMA_COMPAT_MODES)
        raise ValueError(
            f"{SCHEMA_COMPAT_ENV} must be one of: {allowed} (got {mode!r})"
        )
    return normalized


def strict_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with strict-unsupported validation keywords removed."""
    projected = copy.deepcopy(schema)
    _strip_node(projected)
    return projected


def _strip_node(node: Any) -> None:
    if not isinstance(node, dict):
        return
    for keyword in _STRICT_UNSUPPORTED_KEYWORDS:
        node.pop(keyword, None)
    if "const" in node:
        value = node.pop("const")
        node.setdefault("enum", [value])
    for key in _SUBSCHEMA_MAP_KEYS:
        mapping = node.get(key)
        if isinstance(mapping, dict):
            for subschema in mapping.values():
                _strip_node(subschema)
    for key in _SUBSCHEMA_VALUE_KEYS:
        value = node.get(key)
        if isinstance(value, dict):
            _strip_node(value)
        elif isinstance(value, list):
            for subschema in value:
                _strip_node(subschema)
    for key in _SUBSCHEMA_LIST_KEYS:
        values = node.get(key)
        if isinstance(values, list):
            for subschema in values:
                _strip_node(subschema)


def strict_json_schema_model(model: type[BaseModel]) -> type[BaseModel]:
    """Return a subclass whose wire schema is strict-validator compatible.

    The subclass keeps the same fields, validators and name, so the SDK's
    parsed response is still validated (and bounded) by the original model's
    rules.
    """

    def model_json_schema(
        cls: type[BaseModel], *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        del cls
        schema = model.model_json_schema(*args, **kwargs)
        return strict_json_schema(schema)

    return type(
        model.__name__,
        (model,),
        {
            "model_json_schema": classmethod(model_json_schema),
            "__module__": model.__module__,
        },
    )
