"""Agente de operações (Pydantic AI) que vira durável com TemporalDurability.

Modelo padrão: "LLM falso" roteirizado (offline). Real: AGENTE_MODELO=ollama:qwen3:8b
Injeção de falha: AGENTE_FALHAS_LLM=2 (as 2 primeiras chamadas ao LLM caem).
"""

import os

from pydantic_ai import Agent, DeferredToolRequests
from pydantic_ai.durable_exec.temporal import TemporalDurability
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import FunctionModel
from temporalio import activity

FALHAS_DO_LLM = int(os.environ.get("AGENTE_FALHAS_LLM", "0"))


def llm_falso(messages, info) -> ModelResponse:
    """Roteiro: consulta o status, pede para reiniciar, resume."""
    if activity.in_activity() and activity.info().attempt <= FALHAS_DO_LLM:
        print("❌ LLM fora do ar (simulado), o Temporal vai tentar de novo", flush=True)
        raise ConnectionError("provedor de LLM fora do ar")

    retornos = [p for p in messages[-1].parts if isinstance(p, ToolReturnPart)]
    if not retornos:
        chamada = ToolCallPart("consultar_status", {"servico": "api-pagamentos"})
        return ModelResponse(parts=[chamada])
    if retornos[-1].tool_name == "consultar_status":
        chamada = ToolCallPart("reiniciar_servico", {"servico": "api-pagamentos"})
        return ModelResponse(parts=[chamada])
    return ModelResponse(
        parts=[TextPart(f"Resumo: {retornos[-1].tool_name} -> {retornos[-1].content}")]
    )


agente = Agent(
    os.environ.get("AGENTE_MODELO") or FunctionModel(llm_falso),
    name="agente_ops",  # nome estável: identifica as activities no histórico
    instructions="Investigue o serviço com consultar_status e reinicie se estiver degradado.",
    output_type=[str, DeferredToolRequests],
    capabilities=[TemporalDurability()],
)


@agente.tool_plain
async def consultar_status(servico: str) -> str:
    return f"{servico}: degradado (p99 = 4.2s, erros 5xx = 12%)"


@agente.tool_plain(requires_approval=True)  # só roda depois de aprovação humana
async def reiniciar_servico(servico: str) -> str:
    print(f"🔁 reiniciando {servico}", flush=True)
    return f"{servico} reiniciado, latência normalizada"
