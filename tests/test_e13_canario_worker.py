import uuid

from temporalio.worker import Worker

from exemplos.e13_canario_worker import activities as a
from exemplos.e13_canario_worker.workflows import CanarioWorkflow


def test_avaliar_pollers():
    assert a.avaliar("fila", [5.0, 900.0], 60) is None
    assert a.avaliar("fila", [900.0], 60) == "fila: sem pollers nos últimos 60s"
    assert a.avaliar("fila", [], 60) is not None


async def test_workflow_alerta_so_para_fila_sem_poller(env, monkeypatch):
    # O servidor de testes não implementa DescribeTaskQueue: simulamos as idades.
    async def idades_falsas(client, fila):
        return [] if "fantasma" in fila else [1.0]

    monkeypatch.setattr(a, "idades_dos_pollers", idades_falsas)
    fila = f"{uuid.uuid4()}"
    async with Worker(
        env.client, task_queue=fila, workflows=[CanarioWorkflow], activities=[a.checar_filas]
    ):
        alertas = await env.client.execute_workflow(
            CanarioWorkflow.run,
            args=[["ok", "fantasma"], 60],
            id=f"canario-{fila}",
            task_queue=fila,
        )
    assert alertas == ["fantasma: sem pollers nos últimos 60s"]
