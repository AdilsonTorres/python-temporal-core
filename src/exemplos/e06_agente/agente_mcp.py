"""Agente cujas tools vêm de um servidor MCP (stdio). Cada chamada vira activity."""

import sys

from fastmcp.client.transports import StdioTransport
from pydantic_ai import Agent
from pydantic_ai.durable_exec.temporal import TemporalDurability
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import FunctionModel

servidor = StdioTransport(sys.executable, ["-m", "exemplos.e06_agente.mcp_servidor"])


def llm_falso(messages, info) -> ModelResponse:
    retornos = [p for p in messages[-1].parts if isinstance(p, ToolReturnPart)]
    if not retornos:
        chamada = ToolCallPart("consultar_status", {"servico": "api-pagamentos"})
        return ModelResponse(parts=[chamada])
    return ModelResponse(parts=[TextPart(f"Resumo MCP: {retornos[-1].content}")])


agente_mcp = Agent(
    FunctionModel(llm_falso),
    name="agente_mcp",
    toolsets=[MCPToolset(servidor, id="ops")],  # id estável: nomeia as activities
    capabilities=[TemporalDurability()],
)
