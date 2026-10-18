"""Conversa com o workflow de aprovação (use o mesmo ID em todos os comandos).

uv run python -m exemplos.e04_aprovacao.cli pedir deploy-1
uv run python -m exemplos.e04_aprovacao.cli status deploy-1
uv run python -m exemplos.e04_aprovacao.cli aprovar deploy-1 ana     # rejeitado
uv run python -m exemplos.e04_aprovacao.cli aprovar deploy-1 bruno   # ok
uv run python -m exemplos.e04_aprovacao.cli rejeitar deploy-1 bruno  # Signal
"""

import sys

from temporalio.client import WithStartWorkflowOperation, WorkflowUpdateFailedError
from temporalio.common import WorkflowIDConflictPolicy

from exemplos.comum import conectar, rodar

from .worker import TASK_QUEUE
from .workflows import Aprovacao, DeployComAprovacaoWorkflow, PedidoDeploy


async def main(acao: str, workflow_id: str, pessoa: str = "bruno") -> None:
    client = await conectar()

    if acao == "pedir":
        pedido = PedidoDeploy(servico="api-pagamentos", versao="v2.3.0", solicitante="ana")
        # Update-with-Start: inicia (ou reaproveita o ID) e já recebe o estado
        inicio = WithStartWorkflowOperation(
            DeployComAprovacaoWorkflow.run,
            pedido,
            id=workflow_id,
            task_queue=TASK_QUEUE,
            id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
        )
        estado = await client.execute_update_with_start_workflow(
            DeployComAprovacaoWorkflow.registrar_pedido, start_workflow_operation=inicio
        )
        print(f"⏳ {workflow_id}: {estado}")
        return

    handle = client.get_workflow_handle(workflow_id)

    if acao == "status":
        print(f"📋 {await handle.query(DeployComAprovacaoWorkflow.status)}")
    elif acao == "aprovar":
        try:
            await handle.execute_update(
                DeployComAprovacaoWorkflow.aprovar, Aprovacao(aprovador=pessoa)
            )
            print(f"✅ {await handle.result()}")
        except WorkflowUpdateFailedError as erro:
            print(f"❌ update rejeitado: {erro.cause}")
    elif acao == "rejeitar":
        await handle.signal(DeployComAprovacaoWorkflow.rejeitar, pessoa)
        print(f"🛑 {await handle.result()}")


if __name__ == "__main__":
    rodar(main(*sys.argv[1:]))
