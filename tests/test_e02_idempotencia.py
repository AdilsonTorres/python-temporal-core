import uuid

from temporalio.worker import Worker

from exemplos.e02_idempotencia.api import TASK_QUEUE, iniciar_pagamento
from exemplos.e02_idempotencia.workflows import (
    EventoPagamento,
    PagamentoRecebidoWorkflow,
    registrar_pagamento,
)


async def test_mesmo_evento_tres_vezes_um_workflow(env):
    evento_id = f"evt-{uuid.uuid4()}"
    evento = EventoPagamento(evento_id=evento_id, pedido_id="42", valor=350)

    # Sem worker: as três entregas chegam com o workflow ainda em aberto.
    r1 = await iniciar_pagamento(env.client, evento)
    r2 = await iniciar_pagamento(env.client, evento)
    r3 = await iniciar_pagamento(env.client, evento)
    assert r1 == r2 == r3

    async with Worker(
        env.client,
        task_queue=TASK_QUEUE,
        workflows=[PagamentoRecebidoWorkflow],
        activities=[registrar_pagamento],
    ):
        recibo = await env.client.get_workflow_handle(r1["workflow_id"]).result()
    assert recibo == f"recibo-{evento_id}"
