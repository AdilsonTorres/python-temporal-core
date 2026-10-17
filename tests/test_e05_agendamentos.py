import uuid
from datetime import timedelta

from temporalio import activity
from temporalio.worker import Worker

from exemplos.e05_agendamentos.workflows import (
    BoasVindasWorkflow,
    Lembrete,
    LembreteWorkflow,
    RelatorioDiarioWorkflow,
    gerar_relatorio_diario,
)


def criar_worker(env, fila, enviadas):
    # Activity falsa com o mesmo nome: guarda as mensagens em vez de enviar.
    @activity.defn(name="enviar_mensagem")
    async def enviar_mensagem(usuario: str, mensagem: str) -> None:
        enviadas.append(mensagem)

    return Worker(
        env.client,
        task_queue=fila,
        workflows=[LembreteWorkflow, BoasVindasWorkflow, RelatorioDiarioWorkflow],
        activities=[enviar_mensagem, gerar_relatorio_diario],
    )


async def test_lembrete_de_30_dias(env):
    fila, enviadas = str(uuid.uuid4()), []
    lembrete = Lembrete(usuario="ana", mensagem="renovar certificado", em=timedelta(days=30))
    async with criar_worker(env, fila, enviadas):
        inicio = await env.get_current_time()
        resultado = await env.client.execute_workflow(
            LembreteWorkflow.run, lembrete, id=f"lembrete-{fila}", task_queue=fila
        )
    assert resultado == "lembrete enviado"
    assert enviadas == ["renovar certificado"]
    assert await env.get_current_time() - inicio >= timedelta(days=30)


async def test_lembrete_adiado_e_concluido(env):
    fila, enviadas = str(uuid.uuid4()), []
    lembrete = Lembrete(usuario="ana", mensagem="x", em=timedelta(hours=1))
    async with criar_worker(env, fila, enviadas):
        handle = await env.client.start_workflow(
            LembreteWorkflow.run, lembrete, id=f"lembrete-{fila}", task_queue=fila
        )
        await handle.signal(LembreteWorkflow.adiar, timedelta(days=1))
        await handle.signal(LembreteWorkflow.concluir)
        assert await handle.result() == "concluído pelo usuário"
    assert enviadas == []


async def test_boas_vindas_uma_semana_depois(env):
    fila, enviadas = str(uuid.uuid4()), []
    async with criar_worker(env, fila, enviadas):
        await env.client.execute_workflow(
            BoasVindasWorkflow.run, "ana", id=f"bv-{fila}", task_queue=fila
        )
    assert enviadas == ["bem-vinda(o)!", "como está sendo sua primeira semana?"]
