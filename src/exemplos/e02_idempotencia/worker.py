"""uv run python -m exemplos.e02_idempotencia.worker"""

from temporalio.worker import Worker

from exemplos.comum import conectar, rodar

from .api import TASK_QUEUE
from .workflows import PagamentoRecebidoWorkflow, registrar_pagamento


async def main() -> None:
    client = await conectar()
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[PagamentoRecebidoWorkflow],
        activities=[registrar_pagamento],
    )
    print("👷 worker de pagamentos")
    await worker.run()


if __name__ == "__main__":
    rodar(main())
