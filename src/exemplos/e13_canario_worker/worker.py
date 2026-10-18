"""uv run python -m exemplos.e13_canario_worker.worker"""

from temporalio.worker import Worker

from exemplos.comum import conectar, rodar

from .activities import checar_filas
from .workflows import CanarioWorkflow

TASK_QUEUE = "canario"


async def main() -> None:
    client = await conectar()
    worker = Worker(
        client, task_queue=TASK_QUEUE, workflows=[CanarioWorkflow], activities=[checar_filas]
    )
    print("👷 worker do canário (ele mesmo é um poller vivo)")
    await worker.run()


if __name__ == "__main__":
    rodar(main())
