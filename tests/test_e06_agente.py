import uuid

import pytest
import pytest_asyncio
from pydantic_ai.durable_exec.temporal import PydanticAIPlugin
from temporalio.client import WorkflowUpdateFailedError
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from exemplos.e06_agente import agente as modulo_agente
from exemplos.e06_agente.workflows import AgenteMcpWorkflow, AgenteOpsWorkflow, Decisao


@pytest_asyncio.fixture
async def env_agentes():
    """Time-skipping com o plugin do Pydantic AI (conversor de dados + sandbox)."""
    async with await WorkflowEnvironment.start_time_skipping(plugins=[PydanticAIPlugin()]) as env:
        yield env


@pytest.fixture
async def worker(env_agentes):
    tq = str(uuid.uuid4())
    async with Worker(
        env_agentes.client,
        task_queue=tq,
        workflows=[AgenteOpsWorkflow, AgenteMcpWorkflow],
    ):
        yield tq


async def _iniciar(env, tq, workflow_run=AgenteOpsWorkflow.run, pedido="api-pagamentos lenta"):
    return await env.client.start_workflow(
        workflow_run, pedido, id=f"agente-{uuid.uuid4()}", task_queue=tq
    )


async def _esperar_pendencia(handle):
    while not await handle.query(AgenteOpsWorkflow.pendencias):
        await handle.describe()  # cede o loop; o servidor processa o workflow task


async def test_aprovacao_humana_libera_a_acao_perigosa(env_agentes, worker, capsys):
    handle = await _iniciar(env_agentes, worker)
    await _esperar_pendencia(handle)
    assert "reiniciar_servico" in (await handle.query(AgenteOpsWorkflow.pendencias))[0]

    with pytest.raises(WorkflowUpdateFailedError) as erro:
        await handle.execute_update(
            AgenteOpsWorkflow.decidir, Decisao(aprovador="agente_ops", aprovado=True)
        )
    assert "não pode aprovar as próprias ações" in str(erro.value.cause)
    assert "🔁 reiniciando" not in capsys.readouterr().out

    resposta = await handle.execute_update(
        AgenteOpsWorkflow.decidir, Decisao(aprovador="bruno", aprovado=True)
    )
    assert resposta == "✅ aprovado por bruno"
    assert "reiniciado" in await handle.result()


async def test_negacao_nao_executa_a_acao(env_agentes, worker, capsys):
    handle = await _iniciar(env_agentes, worker)
    await _esperar_pendencia(handle)
    await handle.execute_update(
        AgenteOpsWorkflow.decidir, Decisao(aprovador="carla", aprovado=False)
    )
    saida = await handle.result()
    assert "reiniciar_servico" in saida
    assert "reiniciado" not in saida
    assert "🔁 reiniciando" not in capsys.readouterr().out


async def test_queda_do_llm_e_absorvida_pelos_retries(env_agentes, worker, monkeypatch):
    monkeypatch.setattr(modulo_agente, "FALHAS_DO_LLM", 2)  # 2 primeiras tentativas caem
    handle = await _iniciar(env_agentes, worker)
    await _esperar_pendencia(handle)
    await handle.execute_update(
        AgenteOpsWorkflow.decidir, Decisao(aprovador="bruno", aprovado=True)
    )
    assert "reiniciado" in await handle.result()


async def test_tool_mcp_roda_como_activity(env_agentes, worker):
    handle = await _iniciar(env_agentes, worker, AgenteMcpWorkflow.run)
    assert "via MCP" in await handle.result()

    nomes = [
        e.activity_task_scheduled_event_attributes.activity_type.name
        async for e in handle.fetch_history_events()
        if e.HasField("activity_task_scheduled_event_attributes")
    ]
    assert "agent__agente_mcp__mcp_server__ops__call_tool" in nomes
