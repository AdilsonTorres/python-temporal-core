"""Inicia um pedido ao agente e mostra como aprovar.

uv run python -m exemplos.e06_agente.iniciar        # agente de ops (pede aprovação)
uv run python -m exemplos.e06_agente.iniciar mcp    # agente com tools via MCP
"""

import sys
import uuid

from exemplos.comum import rodar

from .worker import TASK_QUEUE, conectar_agentes
from .workflows import AgenteMcpWorkflow, AgenteOpsWorkflow

WORKFLOWS = {"ops": AgenteOpsWorkflow.run, "mcp": AgenteMcpWorkflow.run}


async def main(variante: str = "ops") -> None:
    client = await conectar_agentes()
    wf_id = f"agente-{uuid.uuid4().hex[:6]}"
    workflow_run = WORKFLOWS[variante]
    await client.start_workflow(
        workflow_run, "a api-pagamentos está lenta", id=wf_id, task_queue=TASK_QUEUE
    )
    print(f"🤖 {wf_id}: agente trabalhando")
    if variante == "ops":
        print(f"⏳ para aprovar: uv run python -m exemplos.e06_agente.cli aprovar {wf_id} bruno")


if __name__ == "__main__":
    rodar(main(*sys.argv[1:]))
