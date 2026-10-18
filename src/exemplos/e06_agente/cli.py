"""Conversa com o agente durável.

uv run python -m exemplos.e06_agente.cli pedir agente-1 "a api-pagamentos está lenta"
uv run python -m exemplos.e06_agente.cli pendencias agente-1
uv run python -m exemplos.e06_agente.cli aprovar agente-1 bruno   # ou: negar
"""

import sys

from temporalio.client import WorkflowUpdateFailedError

from exemplos.comum import rodar

from .worker import TASK_QUEUE, conectar_agentes
from .workflows import AgenteOpsWorkflow, Decisao


async def main(acao: str, wf_id: str, arg: str = "bruno") -> None:
    client = await conectar_agentes()

    if acao == "pedir":
        await client.start_workflow(AgenteOpsWorkflow.run, arg, id=wf_id, task_queue=TASK_QUEUE)
        print(f"🤖 {wf_id}: agente trabalhando")
        return

    handle = client.get_workflow_handle(wf_id)
    if acao == "pendencias":
        print("⏳", await handle.query(AgenteOpsWorkflow.pendencias))
    elif acao in ("aprovar", "negar"):
        decisao = Decisao(aprovador=arg, aprovado=(acao == "aprovar"))
        try:
            print(await handle.execute_update(AgenteOpsWorkflow.decidir, decisao))
            print("🤖", await handle.result())
        except WorkflowUpdateFailedError as erro:
            print(f"❌ rejeitado: {erro.cause}")


if __name__ == "__main__":
    rodar(main(*sys.argv[1:]))
