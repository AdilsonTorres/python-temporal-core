"""Webhook do inventário: o id do evento vira o id do workflow (idempotente).

uv run uvicorn exemplos.e10_automacao_rede.api:app --port 8010
curl -X POST localhost:8010/webhooks/inventario -H 'content-type: application/json' \
  -d '{"evento_id": "nb-1", "dispositivo": "sw-01", "novo_nome": "sw-core-01"}'
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from temporalio.common import WorkflowIDConflictPolicy

from exemplos.comum import conectar

from .modelos import EventoRede
from .worker import TASK_QUEUE
from .workflows import RenomearDispositivoWorkflow


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = await conectar()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/webhooks/inventario", status_code=202)
async def webhook_inventario(evento: EventoRede) -> dict:
    handle = await app.state.client.start_workflow(
        RenomearDispositivoWorkflow.run,
        evento,
        id=f"rede-{evento.evento_id}",  # reenvio do webhook não duplica
        task_queue=TASK_QUEUE,
        id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
    )
    return {"workflow_id": handle.id}
