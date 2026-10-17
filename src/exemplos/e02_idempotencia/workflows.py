"""O ID do workflow é a chave de idempotência: mesmo evento, mesmo workflow."""

from datetime import timedelta

from pydantic import BaseModel
from temporalio import activity, workflow


class EventoPagamento(BaseModel):
    evento_id: str
    pedido_id: str
    valor: float


@activity.defn
async def registrar_pagamento(evento: EventoPagamento) -> str:
    print(f"✅ pagamento registrado: pedido {evento.pedido_id}", flush=True)
    return f"recibo-{evento.evento_id}"


@workflow.defn
class PagamentoRecebidoWorkflow:
    @workflow.run
    async def run(self, evento: EventoPagamento) -> str:
        return await workflow.execute_activity(
            registrar_pagamento, evento, start_to_close_timeout=timedelta(seconds=10)
        )
