import asyncio
import uuid

import pytest
from temporalio.client import WorkflowHistory
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Replayer, Worker
from temporalio.workflow import NondeterminismError

from exemplos.e08_versionamento import activities as a
from exemplos.e08_versionamento.modelos import Assinatura
from exemplos.e08_versionamento.v1 import AssinaturaV1
from exemplos.e08_versionamento.v2 import AssinaturaV2
from exemplos.e08_versionamento.v2_quebrado import AssinaturaV2Quebrado

ATIVIDADES = [a.cobrar, a.enviar_lembrete, a.renovar]


async def historico_v1_dormindo(env) -> WorkflowHistory:
    """Roda a v1 até o sleep de 30 dias e devolve o histórico parcial."""
    tq = str(uuid.uuid4())
    async with Worker(env.client, task_queue=tq, workflows=[AssinaturaV1], activities=ATIVIDADES):
        handle = await env.client.start_workflow(
            AssinaturaV1.run, Assinatura(cliente="ana"), id=f"ass-{tq}", task_queue=tq
        )
        with env.auto_time_skipping_disabled():
            while True:  # espera o timer de 30 dias ser agendado (cobrar já concluiu)
                history = await handle.fetch_history()
                if any(e.HasField("timer_started_event_attributes") for e in history.events):
                    break
                await asyncio.sleep(0.05)
        await handle.terminate()
    return WorkflowHistory.from_json(handle.id, history.to_json())


async def test_codigo_novo_com_patched_reproduz_historico_antigo(env):
    history = await historico_v1_dormindo(env)
    await Replayer(
        workflows=[AssinaturaV2], data_converter=pydantic_data_converter
    ).replay_workflow(history)


async def test_mesma_mudanca_sem_patched_quebra_o_replay(env):
    history = await historico_v1_dormindo(env)
    with pytest.raises(NondeterminismError):
        await Replayer(
            workflows=[AssinaturaV2Quebrado], data_converter=pydantic_data_converter
        ).replay_workflow(history)
