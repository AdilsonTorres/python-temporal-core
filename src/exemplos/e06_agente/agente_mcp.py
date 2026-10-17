"""Agente cujas tools vêm de um servidor MCP (stdio). Cada chamada vira activity.

Mesmo AGENTE_MODELO do agente.py (vazio = LLM falso; ollama:/anthropic:/openai:/claude-code).
"""

import os
import sys
from datetime import timedelta

from fastmcp.client.transports import StdioTransport
from pydantic_ai import Agent
from pydantic_ai.durable_exec.temporal import TemporalDurability
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import FunctionModel
from temporalio.workflow import ActivityConfig

from .claude_code import modelo_claude_code

servidor = StdioTransport(sys.executable, ["-m", "exemplos.e06_agente.mcp_servidor"])


def llm_falso(messages, info) -> ModelResponse:
    retornos = [p for p in messages[-1].parts if isinstance(p, ToolReturnPart)]
    if not retornos:
        chamada = ToolCallPart("consultar_status", {"servico": "api-pagamentos"})
        return ModelResponse(parts=[chamada])
    return ModelResponse(parts=[TextPart(f"Resumo MCP: {retornos[-1].content}")])


def escolher_modelo():
    nome = os.environ.get("AGENTE_MODELO")
    if not nome:
        return FunctionModel(llm_falso)
    return modelo_claude_code() if nome == "claude-code" else nome


agente_mcp = Agent(
    escolher_modelo(),
    name="agente_mcp",
    toolsets=[MCPToolset(servidor, id="ops")],  # id estável: nomeia as activities
    capabilities=[
        TemporalDurability(
            model_activity_config=ActivityConfig(start_to_close_timeout=timedelta(seconds=120))
        )
    ],
)
