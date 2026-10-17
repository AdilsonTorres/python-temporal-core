"""Reserva uma viagem; com --falhar-carro o 3º passo falha e tudo é desfeito.

uv run python -m exemplos.e03_saga.iniciar [--falhar-carro]
"""

import sys
import uuid

from temporalio.client import WorkflowFailureError

from exemplos.comum import conectar, rodar

from .activities import Viagem
from .worker import TASK_QUEUE
from .workflows import ReservaViagemWorkflow


async def main(falhar_carro: bool) -> None:
    client = await conectar()
    viagem = Viagem(id=uuid.uuid4().hex[:6], destino="Florianópolis", falhar_carro=falhar_carro)
    try:
        reservas = await client.execute_workflow(
            ReservaViagemWorkflow.run, viagem, id=f"viagem-{viagem.id}", task_queue=TASK_QUEUE
        )
        print(f"🎉 viagem confirmada: {reservas}")
    except WorkflowFailureError as erro:
        causa = erro.cause.cause or erro.cause  # a causa real vem da activity
        print(f"💥 viagem falhou e foi desfeita: {causa}")


if __name__ == "__main__":
    rodar(main("--falhar-carro" in sys.argv))
