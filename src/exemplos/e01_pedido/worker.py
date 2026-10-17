"""Rode o worker, inicie um pedido e mate o worker (kill -9) no meio; suba de novo.

uv run python -m exemplos.e01_pedido.worker
"""

import os

from temporalio.worker import Worker

from exemplos.comum import conectar, rodar

from .activities import cobrar, enviar, notificar_cliente, reservar_estoque, validar_pedido
from .workflows import PedidoWorkflow

TASK_QUEUE = "pedidos"


async def main() -> None:
    client = await conectar()
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[PedidoWorkflow],
        activities=[validar_pedido, cobrar, reservar_estoque, enviar, notificar_cliente],
    )
    print(f"👷 worker de pedidos (pid {os.getpid()}) — Ctrl+C ou kill -9 para parar", flush=True)
    await worker.run()


if __name__ == "__main__":
    rodar(main())
