import asyncio
import uuid
from datetime import timedelta

from temporalio.worker import Worker

from exemplos.e11_lembrete_soneca.activities import notificar
from exemplos.e11_lembrete_soneca.modelos import Lembrete
from exemplos.e11_lembrete_soneca.workflows import LembreteWorkflow


async def esperar_estado(handle, estado: str) -> None:
    while not (await handle.query(LembreteWorkflow.status)).startswith(estado):
        await asyncio.sleep(0.05)


async def test_sonecas_com_continue_as_new(env):
    fila = f"{uuid.uuid4()}"
    lembrete = Lembrete(texto="água", atraso_s=60, soneca_s=30, max_sonecas_por_execucao=2)
    async with Worker(
        env.client, task_queue=fila, workflows=[LembreteWorkflow], activities=[notificar]
    ):
        handle = await env.client.start_workflow(
            LembreteWorkflow.run, lembrete, id=f"lembrete-{fila}", task_queue=fila
        )
        await env.sleep(timedelta(seconds=61))
        for _ in range(3):  # a 3ª soneca já cai na 2ª execução (continue_as_new)
            await esperar_estado(handle, "disparado")
            await handle.signal(LembreteWorkflow.adiar)
            await env.sleep(timedelta(seconds=31))
        await esperar_estado(handle, "disparado")
        await handle.signal(LembreteWorkflow.dispensar)
        assert await handle.result() == "confirmado após 3 sonecas (2 execuções)"


async def test_dispensar_cancela_o_timer(env):
    fila = f"{uuid.uuid4()}"
    async with Worker(
        env.client, task_queue=fila, workflows=[LembreteWorkflow], activities=[notificar]
    ):
        handle = await env.client.start_workflow(
            LembreteWorkflow.run, Lembrete(texto="x"), id=f"lembrete-{fila}", task_queue=fila
        )
        await handle.signal(LembreteWorkflow.dispensar)
        assert await handle.result() == "cancelado antes de disparar"
