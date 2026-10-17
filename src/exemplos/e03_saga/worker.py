"""uv run python -m exemplos.e03_saga.worker"""

from temporalio.worker import Worker

from exemplos.comum import conectar, rodar

from .activities import (
    cancelar_carro,
    cancelar_hotel,
    cancelar_voo,
    reservar_carro,
    reservar_hotel,
    reservar_voo,
)
from .workflows import ReservaViagemWorkflow

TASK_QUEUE = "viagens"
ACTIVITIES = [
    reservar_voo,
    reservar_hotel,
    reservar_carro,
    cancelar_voo,
    cancelar_hotel,
    cancelar_carro,
]


async def main() -> None:
    client = await conectar()
    worker = Worker(
        client, task_queue=TASK_QUEUE, workflows=[ReservaViagemWorkflow], activities=ACTIVITIES
    )
    print("👷 worker de viagens")
    await worker.run()


if __name__ == "__main__":
    rodar(main())
