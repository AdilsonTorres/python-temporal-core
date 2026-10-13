import uuid

from temporalio.worker import Worker

from exemplos.e10_automacao_rede import activities as a
from exemplos.e10_automacao_rede.modelos import EventoRede
from exemplos.e10_automacao_rede.worker import ACTIVITIES
from exemplos.e10_automacao_rede.workflows import RenomearDispositivoWorkflow


async def rodar_evento(env, evento: EventoRede) -> str:
    fila = f"{uuid.uuid4()}"
    async with Worker(
        env.client, task_queue=fila, workflows=[RenomearDispositivoWorkflow], activities=ACTIVITIES
    ):
        return await env.client.execute_workflow(
            RenomearDispositivoWorkflow.run, evento, id=f"rede-{fila}", task_queue=fila
        )


async def test_renomeia_dispositivo(env):
    a.EQUIPAMENTOS["sw-01"] = "sw-01"
    evento = EventoRede(evento_id="1", dispositivo="sw-01", novo_nome="sw-core-01")
    assert await rodar_evento(env, evento) == "renomeado"
    assert a.EQUIPAMENTOS["sw-01"] == "sw-core-01"


async def test_verificacao_falha_faz_rollback(env):
    a.EQUIPAMENTOS["sw-01"] = "sw-01"
    evento = EventoRede(
        evento_id="2", dispositivo="sw-01", novo_nome="sw-core-01", falhar_verificacao=True
    )
    assert await rodar_evento(env, evento) == "revertido"
    assert a.EQUIPAMENTOS["sw-01"] == "sw-01"
