"""Webhook que inicia o workflow de forma idempotente.

    uv run uvicorn exemplos.e02_idempotencia.api:app --port 8000
    curl -X POST localhost:8000/webhooks/pagamento -H 'content-type: application/json' \
      -d '{"evento_id": "evt_123", "pedido_id": "42", "valor": 350}'
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from temporalio.client import Client
from temporalio.common import WorkflowIDConflictPolicy, WorkflowIDReusePolicy
from temporalio.exceptions import WorkflowAlreadyStartedError

from exemplos.comum import conectar

from .workflows import EventoPagamento, PagamentoRecebidoWorkflow

TASK_QUEUE = "pagamentos"


async def iniciar_pagamento(client: Client, evento: EventoPagamento) -> dict:
    workflow_id = f"pagamento-{evento.evento_id}"  # a chave de idempotência
    try:
        handle = await client.start_workflow(
            PagamentoRecebidoWorkflow.run,
            evento,
            id=workflow_id,
            task_queue=TASK_QUEUE,
            # Já está rodando? Reaproveita. Já terminou? Rejeita.
            id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
            id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
        )
    except WorkflowAlreadyStartedError:
        return {"workflow_id": workflow_id, "duplicado": True}
    return {"workflow_id": handle.id, "run_id": handle.result_run_id}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = await conectar()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/webhooks/pagamento", status_code=202)
async def webhook_pagamento(evento: EventoPagamento) -> dict:
    return await iniciar_pagamento(app.state.client, evento)
