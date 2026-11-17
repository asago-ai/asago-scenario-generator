"""Strict-validator wire schema projection for structured responses."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from asago_scenario_generator.llm import client as client_module
from asago_scenario_generator.llm.client import LLMClient
from asago_scenario_generator.llm.schema_compat import (
    SCHEMA_COMPAT_ENV,
    resolve_schema_compat,
    strict_json_schema,
    strict_json_schema_model,
)
from asago_scenario_generator.pipeline.generate.behavior_semantics import (
    BehaviorDraftV2,
    build_behavior_draft_response_model,
)

UNSUPPORTED = {
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
    "propertyNames",
    "patternProperties",
}


def _schema_keywords(value: object) -> set[str]:
    keys: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            keys.update(node.keys())
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    return keys


def test_resolve_schema_compat_defaults_to_native(monkeypatch):
    monkeypatch.delenv(SCHEMA_COMPAT_ENV, raising=False)
    assert resolve_schema_compat() == "native"


def test_resolve_schema_compat_reads_env_and_validates(monkeypatch):
    monkeypatch.setenv(SCHEMA_COMPAT_ENV, "STRICT")
    assert resolve_schema_compat() == "strict"
    with pytest.raises(ValueError, match="must be one of"):
        resolve_schema_compat("lenient")


def test_dynamic_handles_schema_is_strict_compatible():
    model = build_behavior_draft_response_model(
        tuple(f"a{i}" for i in range(10)), examples_allowed=False
    )
    strict = strict_json_schema_model(model).model_json_schema()
    assert not (_schema_keywords(strict) & UNSUPPORTED)
    assert "maxProperties" in _schema_keywords(model.model_json_schema())


def test_examples_allowed_schema_is_strict_compatible():
    model = build_behavior_draft_response_model(
        tuple(f"a{i}" for i in range(10)), examples_allowed=True
    )
    strict = strict_json_schema_model(model).model_json_schema()
    assert not (_schema_keywords(strict) & UNSUPPORTED)


def test_strict_projection_keeps_local_validation():
    strict_model = strict_json_schema_model(BehaviorDraftV2)
    valid = {
        "scenarios": [
            {
                "title": "Title",
                "steps": [{"kind": "action", "handle": "a0", "text": "Act"}],
            }
        ]
    }
    strict_model.model_validate(valid)
    with pytest.raises(ValidationError):
        strict_model.model_validate(
            {
                "scenarios": [
                    {
                        "title": "x" * 161,
                        "steps": [{"kind": "action", "handle": "a0", "text": "Act"}],
                    }
                ]
            }
        )


def test_strict_projection_handles_const():
    schema = {"type": "object", "properties": {"kind": {"const": "action"}}}
    assert strict_json_schema(schema)["properties"]["kind"] == {"enum": ["action"]}


class _StopRequest(Exception):
    pass


def _capturing_request_completion(monkeypatch):
    captured: dict[str, object] = {}

    def fake(client, model, messages, response_format, extra_kwargs):
        captured["response_format"] = response_format
        raise _StopRequest

    monkeypatch.setattr(client_module, "_request_completion", fake)
    return captured


def test_client_uses_strict_wire_format(monkeypatch):
    captured = _capturing_request_completion(monkeypatch)
    client = LLMClient(
        base_url="https://example.invalid/v1",
        api_key="not-needed",
        model="model",
        schema_compat="strict",
    )
    with pytest.raises(_StopRequest):
        client._complete([], BehaviorDraftV2, {})
    schema = captured["response_format"].model_json_schema()
    assert not (_schema_keywords(schema) & UNSUPPORTED)


def test_client_keeps_native_format_by_default(monkeypatch):
    captured = _capturing_request_completion(monkeypatch)
    client = LLMClient(
        base_url="https://example.invalid/v1",
        api_key="not-needed",
        model="model",
    )
    with pytest.raises(_StopRequest):
        client._complete([], BehaviorDraftV2, {})
    assert captured["response_format"] is BehaviorDraftV2


def test_stpa_client_resolves_schema_compat(monkeypatch):
    from asago_scenario_generator.stpa.infra.llm import LLMClient as StpaClient

    monkeypatch.setenv(SCHEMA_COMPAT_ENV, "strict")
    client = StpaClient(
        base_url="https://example.invalid/v1",
        api_key="not-needed",
        model="model",
    )
    assert client.schema_compat == "strict"


def test_stpa_and_taxonomy_schema_projections_match():
    from asago_scenario_generator.stpa.infra import schema_compat as stpa

    model = build_behavior_draft_response_model(
        tuple(f"a{i}" for i in range(10)), examples_allowed=True
    )
    schema = model.model_json_schema()
    assert stpa.strict_json_schema(schema) == strict_json_schema(schema)
