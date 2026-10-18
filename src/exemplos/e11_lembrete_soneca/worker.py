"""uv run python -m exemplos.e11_lembrete_soneca.worker"""

from temporalio.worker import Worker

from exemplos.comum import conectar, rodar

from .activities import notificar
from .workflows import LembreteWorkflow

TASK_QUEUE = "lembrete"


async def main() -> None:
    client = await conectar()
    worker = Worker(
        client, task_queue=TASK_QUEUE, workflows=[LembreteWorkflow], activities=[notificar]
    )
    print("👷 worker de lembretes")
    await worker.run()


if __name__ == "__main__":
    rodar(main())
