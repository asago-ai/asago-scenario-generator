"""Wire-schema compatibility for OpenAI-strict structured outputs.

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
from functools import lru_cache
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
        "discriminator",
        "prefixItems",
    }
)

_SUBSCHEMA_MAP_KEYS = ("properties", "$defs", "definitions", "dependentSchemas")
_SUBSCHEMA_VALUE_KEYS = (
    "items",
    "additionalProperties",
    "additionalItems",
    "not",
    "contains",
    "if",
    "then",
    "else",
    "unevaluatedProperties",
    "unevaluatedItems",
    "contentSchema",
)
_SUBSCHEMA_LIST_KEYS = ("anyOf", "allOf")


def resolve_schema_compat(value: str | None = None) -> str:
    """Resolve the mode from an explicit value or the environment."""
    mode = value if value is not None else os.environ.get(SCHEMA_COMPAT_ENV)
    if not mode:
        return SCHEMA_COMPAT_NATIVE
    normalized = mode.strip().lower()
    if normalized not in SCHEMA_COMPAT_MODES:
        allowed = ", ".join(SCHEMA_COMPAT_MODES)
        source = "schema_compat" if value is not None else SCHEMA_COMPAT_ENV
        raise ValueError(f"{source} must be one of: {allowed} (got {mode!r})")
    return normalized


def strict_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with strict-unsupported validation keywords removed."""
    projected = copy.deepcopy(schema)
    _strip_node(projected)
    return projected


def _append_limit_hint(node: dict[str, Any], keyword: str, label: str) -> None:
    limit = node.get(keyword)
    if not isinstance(limit, int):
        return
    hint = f"Maximum {limit} {label}."
    description = str(node.get("description") or "").strip()
    if hint not in description:
        node["description"] = f"{description} {hint}".strip()


def _strip_node(node: Any) -> None:
    if not isinstance(node, dict):
        return
    # Preserve the useful part of local bounds in the prompt-facing
    # description; strict validators do not accept the keywords themselves.
    _append_limit_hint(node, "maxLength", "characters")
    _append_limit_hint(node, "maxItems", "items")
    _append_limit_hint(node, "maxProperties", "properties")
    for keyword in _STRICT_UNSUPPORTED_KEYWORDS:
        node.pop(keyword, None)
    if "const" in node:
        value = node.pop("const")
        node.setdefault("enum", [value])
    # Strict validators support anyOf, not oneOf. The variants remain
    # locally validated by Pydantic after parsing.
    one_of = node.pop("oneOf", None)
    if one_of is not None and "anyOf" not in node:
        node["anyOf"] = one_of
    for key in _SUBSCHEMA_MAP_KEYS:
        mapping = node.get(key)
        if isinstance(mapping, dict):
            # Strict validators reject the open-object shape used by the
            # optional ``examples`` map. Local validation supplies the
            # model's empty default when the wire schema omits it.
            if key == "properties" and "examples" in mapping:
                mapping.pop("examples")
                required = node.get("required")
                if isinstance(required, list):
                    node["required"] = [item for item in required if item != "examples"]
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
    # ``oneOf`` is traversed before it is converted to anyOf above.
    if isinstance(one_of, list):
        for subschema in one_of:
            _strip_node(subschema)


@lru_cache(maxsize=256)
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
