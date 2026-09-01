import asyncio
from types import SimpleNamespace

from app.agents import scope_guardrail


def test_scope_guardrail_blocks_out_of_scope_message(monkeypatch) -> None:
    async def fake_runner_run(*args, **kwargs):
        return SimpleNamespace(final_output=scope_guardrail.ScopeCheck(is_in_scope=False))

    monkeypatch.setattr(scope_guardrail.Runner, "run", fake_runner_run)

    result = asyncio.run(
        scope_guardrail.finance_scope_guardrail.guardrail_function(
            SimpleNamespace(context=None), None, "Gere um codigo DFS em Python"
        )
    )

    assert result.tripwire_triggered is True


def test_scope_guardrail_allows_greeting_without_calling_model(monkeypatch) -> None:
    async def unexpected_runner_run(*args, **kwargs):
        raise AssertionError("The guardrail model should not run for a greeting")

    monkeypatch.setattr(scope_guardrail.Runner, "run", unexpected_runner_run)

    result = asyncio.run(
        scope_guardrail.finance_scope_guardrail.guardrail_function(
            SimpleNamespace(context=None), None, "Ol\u00e1"
        )
    )

    assert result.tripwire_triggered is False
