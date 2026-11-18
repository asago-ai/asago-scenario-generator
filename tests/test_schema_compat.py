"""Strict-validator wire schema projection for structured responses."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from asago_scenario_generator.llm import client as client_module
from asago_scenario_generator.llm.client import LLMClient
from asago_scenario_generator.llm.schema_compat import (
    SCHEMA_COMPAT_ENV,
    SCHEMA_COMPAT_NATIVE,
    _STRICT_UNSUPPORTED_KEYWORDS,
    resolve_schema_compat,
    strict_json_schema,
    strict_json_schema_model,
)
from asago_scenario_generator.pipeline.generate.behavior_semantics import (
    BehaviorDraftV2,
    build_behavior_draft_response_model,
)

UNSUPPORTED = set(_STRICT_UNSUPPORTED_KEYWORDS) - {
    "examples"
}  # a property may be named examples


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


def test_strict_projection_converts_one_of_and_strips_children():
    schema = {
        "oneOf": [
            {"type": "string", "maxLength": 4},
            {"type": "integer", "minimum": 0},
        ],
        "discriminator": {"propertyName": "kind"},
    }
    projected = strict_json_schema(schema)
    assert "oneOf" not in projected and "discriminator" not in projected
    assert projected["anyOf"][0]["type"] == "string"
    assert projected["anyOf"][0]["description"] == "Maximum 4 characters."
    assert projected["anyOf"][1] == {"type": "integer"}


def test_strict_projection_removes_prefix_items():
    schema = {"type": "array", "prefixItems": [{"type": "string", "maxLength": 2}]}
    assert "prefixItems" not in strict_json_schema(schema)


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
    monkeypatch.delenv(SCHEMA_COMPAT_ENV, raising=False)
    captured = _capturing_request_completion(monkeypatch)
    client = LLMClient(
        base_url="https://example.invalid/v1",
        api_key="not-needed",
        model="model",
    )
    with pytest.raises(_StopRequest):
        client._complete([], BehaviorDraftV2, {})
    assert captured["response_format"] is BehaviorDraftV2


def test_client_without_init_defaults_to_native():
    """Acceptance fixtures build clients without __init__; they must not crash."""
    client = LLMClient.__new__(LLMClient)
    assert client.schema_compat == SCHEMA_COMPAT_NATIVE


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


def test_resume_client_keeps_persisted_schema_mode():
    from asago_scenario_generator.pipeline.runner_resume import _resume_llm_client

    client = _resume_llm_client(
        "https://example.invalid/v1",
        "not-needed",
        "model",
        None,
        schema_compat="strict",
    )
    assert client.schema_compat == "strict"


def test_generate_cli_exposes_schema_compat_flag():
    import typer.main

    from asago_scenario_generator.cli import app

    # Inspect the registered command rather than the rendered help: Rich
    # truncates long option names on narrow, non-tty terminals, which made
    # the help-text assertion fail in CI while passing locally.
    group = typer.main.get_command(app)
    options = {opt for param in group.commands["generate"].params for opt in param.opts}
    assert "--json-schema-compat" in options


def test_strict_projection_drops_open_examples_and_keeps_hints():
    model = build_behavior_draft_response_model(
        tuple(f"a{i}" for i in range(4)), examples_allowed=True
    )
    strict = strict_json_schema_model(model).model_json_schema()
    step = strict["$defs"]["BehaviorDraftStep"]
    assert "examples" not in step["properties"]
    assert "examples" not in step["required"]
    # The removed maxLength still gives the model a human-readable bound.
    assert "Maximum 500 characters." in step["properties"]["text"]["description"]
