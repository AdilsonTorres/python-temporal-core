"""Workflows: o laço do agente roda no workflow e pausa até um humano aprovar."""

from pydantic import BaseModel
from pydantic_ai import DeferredToolRequests, DeferredToolResults
from pydantic_ai.durable_exec.temporal import PydanticAIWorkflow
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .agente import agente
    from .agente_mcp import agente_mcp


class Decisao(BaseModel):
    aprovador: str
    aprovado: bool


@workflow.defn
class AgenteOpsWorkflow(PydanticAIWorkflow):
    __pydantic_ai_agents__ = [agente]  # registra as activities do agente

    def __init__(self) -> None:
        self.pendentes: list[str] = []
        self.decisao: Decisao | None = None

    @workflow.run
    async def run(self, pedido: str) -> str:
        resultado = await agente.run(pedido)

        while isinstance(resultado.output, DeferredToolRequests):
            pedidos = resultado.output.approvals
            self.pendentes = [f"{c.tool_name}({c.args_as_dict()})" for c in pedidos]
            await workflow.wait_condition(lambda: self.decisao is not None)
            aprovado = self.decisao.aprovado
            self.decisao, self.pendentes = None, []

            resultado = await agente.run(
                message_history=resultado.all_messages(),
                deferred_tool_results=DeferredToolResults(
                    approvals={c.tool_call_id: aprovado for c in pedidos}
                ),
            )
        return resultado.output

    @workflow.update
    def decidir(self, decisao: Decisao) -> str:
        self.decisao = decisao
        if decisao.aprovado:
            return f"✅ aprovado por {decisao.aprovador}"
        return f"❌ negado por {decisao.aprovador}"

    @decidir.validator
    def validar_decisao(self, decisao: Decisao) -> None:
        if not self.pendentes:
            raise ValueError("não há nada aguardando aprovação")
        if decisao.aprovador == "agente_ops":
            raise ValueError("o agente não pode aprovar as próprias ações")

    @workflow.query
    def pendencias(self) -> list[str]:
        return self.pendentes


@workflow.defn
class AgenteMcpWorkflow(PydanticAIWorkflow):
    __pydantic_ai_agents__ = [agente_mcp]

    @workflow.run
    async def run(self, pedido: str) -> str:
        return (await agente_mcp.run(pedido)).output
