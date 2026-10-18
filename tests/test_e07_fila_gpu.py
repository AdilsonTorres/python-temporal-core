import uuid

from temporalio import activity
from temporalio.worker import Worker

from exemplos.e07_fila_gpu import activities as a
from exemplos.e07_fila_gpu.worker import (
    MAX_INFERENCIAS_SIMULTANEAS,
    TASK_QUEUE,
    criar_worker,
)
from exemplos.e07_fila_gpu.workflows import InferenciaWorkflow


async def test_backend_fora_do_ar_espera_e_completa(env, monkeypatch):
    tentativas = []

    async def backend_instavel(prompt: str) -> str:
        tentativas.append(activity.info().attempt)
        if activity.info().attempt <= 3:
            raise ConnectionError("backend fora do ar (modo gaming)")
        return f"eco: {prompt}"

    monkeypatch.setattr(a, "_chamar_backend", backend_instavel)

    tq = str(uuid.uuid4())
    async with Worker(
        env.client,
        task_queue=tq,
        workflows=[InferenciaWorkflow],
        activities=[a.gerar_resposta],
        max_concurrent_activities=MAX_INFERENCIAS_SIMULTANEAS,
    ):
        resultado = await env.client.execute_workflow(
            InferenciaWorkflow.run, "oi", id=f"inf-{tq}", task_queue=tq
        )

    assert tentativas == [1, 2, 3, 4]  # esperou o backend voltar em vez de falhar
    assert resultado == "eco: oi"


async def test_worker_processa_uma_inferencia_por_vez(env):
    assert MAX_INFERENCIAS_SIMULTANEAS == 1
    assert TASK_QUEUE == "fila-gpu"
    worker = criar_worker(env.client)
    assert worker.config()["max_concurrent_activities"] == 1
