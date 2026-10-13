import uuid

import pytest
from temporalio.client import WorkflowUpdateFailedError
from temporalio.worker import Worker

from exemplos.e14_entidade_carrinho.activities import registrar_pedido
from exemplos.e14_entidade_carrinho.modelos import Carrinho, Item
from exemplos.e14_entidade_carrinho.workflows import CarrinhoWorkflow

TECLADO = Item(sku="teclado", quantidade=1, preco=250)
MOUSE = Item(sku="mouse", quantidade=2, preco=50)


async def abrir(env, fila: str):
    return await env.client.start_workflow(
        CarrinhoWorkflow.run, Carrinho(cliente="ana"), id=f"carrinho-{fila}", task_queue=fila
    )


async def test_adiciona_remove_e_fecha(env):
    fila = f"{uuid.uuid4()}"
    async with Worker(
        env.client, task_queue=fila, workflows=[CarrinhoWorkflow], activities=[registrar_pedido]
    ):
        handle = await abrir(env, fila)
        assert await handle.execute_update(CarrinhoWorkflow.adicionar, TECLADO) == 250
        assert await handle.execute_update(CarrinhoWorkflow.adicionar, MOUSE) == 350
        assert await handle.query(CarrinhoWorkflow.total) == 350
        with pytest.raises(WorkflowUpdateFailedError):  # recusado pelo validador
            await handle.execute_update(CarrinhoWorkflow.remover, "inexistente")
        assert await handle.execute_update(CarrinhoWorkflow.remover, "mouse") == 250
        await handle.execute_update(CarrinhoWorkflow.fechar)
        assert await handle.result() == "fechado: R$ 250.00"


async def test_validador_recusa_quantidade_zero(env):
    fila = f"{uuid.uuid4()}"
    async with Worker(
        env.client, task_queue=fila, workflows=[CarrinhoWorkflow], activities=[registrar_pedido]
    ):
        handle = await abrir(env, fila)
        with pytest.raises(WorkflowUpdateFailedError):
            await handle.execute_update(
                CarrinhoWorkflow.adicionar, Item(sku="x", quantidade=0, preco=1)
            )
        assert await handle.query(CarrinhoWorkflow.total) == 0


async def test_carrinho_ocioso_por_um_dia_e_abandonado(env):
    fila = f"{uuid.uuid4()}"
    async with Worker(
        env.client, task_queue=fila, workflows=[CarrinhoWorkflow], activities=[registrar_pedido]
    ):
        handle = await abrir(env, fila)
        await handle.execute_update(CarrinhoWorkflow.adicionar, TECLADO)
        assert await handle.result() == "abandonado"  # time-skipping: 1 dia em ms
