"""Canário: pergunta ao servidor quem está fazendo poll em cada task queue."""

from datetime import UTC, datetime

from temporalio import activity
from temporalio.api.enums.v1 import TaskQueueType
from temporalio.api.taskqueue.v1 import TaskQueue
from temporalio.api.workflowservice.v1 import DescribeTaskQueueRequest
from temporalio.client import Client


async def idades_dos_pollers(client: Client, fila: str) -> list[float]:
    # No SDK 1.34 não há método de alto nível: usa o serviço gRPC direto.
    resposta = await client.workflow_service.describe_task_queue(
        DescribeTaskQueueRequest(
            namespace=client.namespace,
            task_queue=TaskQueue(name=fila),
            task_queue_type=TaskQueueType.TASK_QUEUE_TYPE_WORKFLOW,
            report_pollers=True,
        )
    )
    agora = datetime.now(UTC)
    return [
        (agora - p.last_access_time.ToDatetime(tzinfo=UTC)).total_seconds()
        for p in resposta.pollers
    ]


def avaliar(fila: str, idades: list[float], janela_s: int) -> str | None:
    if any(idade <= janela_s for idade in idades):
        return None
    return f"{fila}: sem pollers nos últimos {janela_s}s"


@activity.defn
async def checar_filas(filas: list[str], janela_s: int) -> list[str]:
    alertas = []
    for fila in filas:
        alerta = avaliar(fila, await idades_dos_pollers(activity.client(), fila), janela_s)
        print(f"🚨 ALERTA: {alerta}" if alerta else f"✅ {fila}: poller vivo", flush=True)
        if alerta:
            alertas.append(alerta)
    return alertas
