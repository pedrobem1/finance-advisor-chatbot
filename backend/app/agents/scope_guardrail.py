from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, Runner, TResponseInputItem
from agents.decorators import input_guardrail
from pydantic import BaseModel


CASUAL_MESSAGES = {
    "oi",
    "ola",
    "olá",
    "bom dia",
    "boa tarde",
    "boa noite",
    "tudo bem",
    "obrigado",
    "obrigada",
    "valeu",
}


class ScopeCheck(BaseModel):
    is_in_scope: bool


scope_agent = Agent(
    name="Finance Scope Guardrail",
    instructions=(
        "Classifique se a mensagem esta dentro do escopo de um chatbot financeiro. "
        "Aceite saudacoes, agradecimentos e mensagens curtas de conversa, pois o "
        "assistente pode se apresentar e orientar o usuario sobre o escopo. Tambem aceite mensagens que " \
        "parecem de continuidade de conversa, como Gere um grafico disso, Nao entendi, etc. "
        "Aceite perguntas sobre financas, investimentos, mercado, economia, empresas, "
        "acoes, ETFs, FIIs, indicadores, dividendos, noticias financeiras e sobre o "
        "funcionamento deste chatbot. Aceite programacao somente quando estiver ligada "
        "diretamente a analise financeira. Rejeite programacao generica, deveres, "
        "entretenimento e qualquer outro assunto sem relacao com financas ou com a conversa."
    ),
    output_type=ScopeCheck,
)


@input_guardrail(run_in_parallel=False)
async def finance_scope_guardrail(
    ctx: RunContextWrapper[None],
    _: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    if isinstance(input, str) and input.strip().casefold() in CASUAL_MESSAGES:
        return GuardrailFunctionOutput(
            output_info=ScopeCheck(is_in_scope=True),
            tripwire_triggered=False,
        )

    result = await Runner.run(scope_agent, input, context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.is_in_scope,
    )
