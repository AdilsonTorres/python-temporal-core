import uuid

from temporalio import activity
from temporalio.client import WorkflowHistory
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Replayer, Worker

from exemplos.e01_pedido import activities as a
from exemplos.e01_pedido.modelos import Pedido
from exemplos.e01_pedido.workflows import PedidoWorkflow

PEDIDO = Pedido(id="42", cliente="ana", itens=["teclado"], valor=10.0)


async def test_pedido_com_gateway_instavel(env, monkeypatch):
    monkeypatch.setattr(a, "DEMORA", 0)
    tentativas = []

    # Activity falsa com o mesmo nome: falha 2 vezes e depois funciona.
    @activity.defn(name="cobrar")
    async def cobrar_instavel(pedido: Pedido) -> str:
        tentativas.append(activity.info().attempt)
        if activity.info().attempt < 3:
            raise ConnectionError("timeout")
        return "pag-42"

    fila = str(uuid.uuid4())
    async with Worker(
        env.client,
        task_queue=fila,
        workflows=[PedidoWorkflow],
        activities=[
            a.validar_pedido,
            cobrar_instavel,
            a.reservar_estoque,
            a.enviar,
            a.notificar_cliente,
        ],
    ):
        handle = await env.client.start_workflow(
            PedidoWorkflow.run, PEDIDO, id=f"pedido-{fila}", task_queue=fila
        )
        resultado = await handle.result()
        historico = await handle.fetch_history()

    assert tentativas == [1, 2, 3]  # o retry é do Temporal, não do nosso código
    assert resultado.pagamento_id == "pag-42"
    assert resultado.rastreio == "BR42"

    # Replay: o código atual reproduz o histórico gravado (determinismo).
    replayer = Replayer(workflows=[PedidoWorkflow], data_converter=pydantic_data_converter)
    await replayer.replay_workflow(WorkflowHistory.from_json(handle.id, historico.to_json()))
