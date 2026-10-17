import uuid
from datetime import timedelta

import pytest
from temporalio.client import WithStartWorkflowOperation, WorkflowUpdateFailedError
from temporalio.common import WorkflowIDConflictPolicy
from temporalio.worker import Worker

from exemplos.e04_aprovacao.workflows import (
    Aprovacao,
    DeployComAprovacaoWorkflow,
    PedidoDeploy,
    fazer_deploy,
)

PEDIDO = PedidoDeploy(servico="api", versao="v2", solicitante="ana")


@pytest.fixture
async def handle(env):
    fila = str(uuid.uuid4())
    async with Worker(
        env.client,
        task_queue=fila,
        workflows=[DeployComAprovacaoWorkflow],
        activities=[fazer_deploy],
    ):
        yield await env.client.start_workflow(
            DeployComAprovacaoWorkflow.run, PEDIDO, id=f"deploy-{fila}", task_queue=fila
        )


async def test_validador_bloqueia_auto_aprovacao(handle):
    with pytest.raises(WorkflowUpdateFailedError) as erro:
        await handle.execute_update(DeployComAprovacaoWorkflow.aprovar, Aprovacao(aprovador="ana"))
    assert "próprio deploy" in str(erro.value.cause)
    assert await handle.query(DeployComAprovacaoWorkflow.status) == "aguardando aprovação"

    resposta = await handle.execute_update(
        DeployComAprovacaoWorkflow.aprovar, Aprovacao(aprovador="bruno")
    )
    assert resposta == "aprovado por bruno"
    assert await handle.result() == "api@v2 no ar (aprovado por bruno)"


async def test_rejeicao_por_signal(handle):
    await handle.signal(DeployComAprovacaoWorkflow.rejeitar, "carla")
    assert await handle.result() == "rejeitado por carla"


async def test_expira_em_3_dias(env, handle):
    inicio = await env.get_current_time()
    assert await handle.result() == "rejeitado: ninguém aprovou em 3 dias"
    assert await env.get_current_time() - inicio >= timedelta(days=3)


async def test_update_with_start_e_idempotente(env):
    fila = str(uuid.uuid4())
    async with Worker(
        env.client,
        task_queue=fila,
        workflows=[DeployComAprovacaoWorkflow],
        activities=[fazer_deploy],
    ):
        runs = []
        for _ in range(2):  # pedir duas vezes com o mesmo ID: um workflow só
            inicio = WithStartWorkflowOperation(
                DeployComAprovacaoWorkflow.run,
                PEDIDO,
                id=f"deploy-{fila}",
                task_queue=fila,
                id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
            )
            estado = await env.client.execute_update_with_start_workflow(
                DeployComAprovacaoWorkflow.registrar_pedido, start_workflow_operation=inicio
            )
            assert estado == "aguardando aprovação (pedido por ana)"
            handle = await inicio.workflow_handle()
            runs.append(handle.result_run_id)
        assert runs[0] == runs[1]
        await handle.signal(DeployComAprovacaoWorkflow.rejeitar, "carla")  # encerra o workflow
        assert await handle.result() == "rejeitado por carla"
