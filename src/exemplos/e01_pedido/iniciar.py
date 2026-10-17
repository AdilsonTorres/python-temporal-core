"""Inicia um pedido e espera o resultado.

uv run python -m exemplos.e01_pedido.iniciar [pedido_id]
"""

import sys

from exemplos.comum import conectar, rodar

from .modelos import Pedido
from .worker import TASK_QUEUE
from .workflows import PedidoWorkflow


async def main(pedido_id: str) -> None:
    client = await conectar()
    pedido = Pedido(id=pedido_id, cliente="ana", itens=["teclado", "mouse"], valor=350.0)
    handle = await client.start_workflow(
        PedidoWorkflow.run, pedido, id=f"pedido-{pedido_id}", task_queue=TASK_QUEUE
    )
    print(f"🚀 iniciado: {handle.id} (UI: http://localhost:8233)")
    resultado = await handle.result()
    print(f"🎉 concluído: {resultado.model_dump()}")


if __name__ == "__main__":
    rodar(main(sys.argv[1] if len(sys.argv) > 1 else "42"))
